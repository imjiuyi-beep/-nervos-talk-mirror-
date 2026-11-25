const { execSync } = require('child_process');
const bitcoin = require('bitcoinjs-lib');
const { ECPairFactory } = require('ecpair');
const ecc = require('tiny-secp256k1');
const crypto = require('crypto');
const ECPair = ECPairFactory(ecc);
const network = bitcoin.networks.regtest;
const OP = bitcoin.opcodes;

const DD = '/tmp/btcdata';
const cli = c => execSync(`bitcoin-cli -regtest -datadir=${DD} ${c}`).toString().trim();
const cliJ = c => JSON.parse(cli(c));

function buildHtlc(hash, alicePub, bobPub, lockTime) {
  return bitcoin.script.compile([
    OP.OP_IF, OP.OP_SHA256, hash, OP.OP_EQUALVERIFY, alicePub,
    OP.OP_ELSE, bitcoin.script.number.encode(lockTime), OP.OP_CHECKLOCKTIMEVERIFY, OP.OP_DROP, bobPub,
    OP.OP_ENDIF, OP.OP_CHECKSIG,
  ]);
}

function spendP2wsh({ utxo, script, value, signer, witnessExtra, destAddr, fee }) {
  const tx = new bitcoin.Transaction();
  tx.version = 2;
  tx.addInput(Buffer.from(utxo.txid, 'hex').reverse(), utxo.vout);
  tx.addOutput(bitcoin.address.toOutputScript(destAddr, network), value - fee);
  const sigHash = tx.hashForWitnessV0(0, script, value, bitcoin.Transaction.SIGHASH_ALL);
  const sig = signer.sign(sigHash);
  const sigEnc = bitcoin.script.signature.encode(Buffer.from(sig), bitcoin.Transaction.SIGHASH_ALL);
  tx.setWitness(0, [sigEnc, ...witnessExtra, script]);
  return tx;
}

(async () => {
  const preimage = crypto.randomBytes(32);
  const hash = crypto.createHash('sha256').update(preimage).digest();
  const alice = ECPair.makeRandom({ network });
  const bob = ECPair.makeRandom({ network });
  const lockTime = 200;
  const script = buildHtlc(hash, alice.publicKey, bob.publicKey, lockTime);
  const p2wsh = bitcoin.payments.p2wsh({ redeem: { output: script, network }, network });
  console.log('HTLC P2WSH:', p2wsh.address);

  // fund 2 BTC
  cli(`sendtoaddress ${p2wsh.address} 2`);
  cli(`generatetoaddress 1 ${cli('getnewaddress')}`);
  const scan = cliJ(`scantxoutset start '["addr(${p2wsh.address})"]'`);
  const utxo = scan.unspents[0];
  const value = Math.round(utxo.amount * 1e8);
  console.log('UTXO:', utxo.txid, 'vout', utxo.vout, 'value', utxo.amount, 'BTC');

  const dest = cli('getnewaddress');
  const destBefore = cliJ(`getreceivedbyaddress ${dest}`);

  // 反例：错误 preimage 应被脚本拒绝
  let badRejected = false;
  try {
    const badTx = spendP2wsh({ utxo, script, value, signer: alice, witnessExtra: [crypto.randomBytes(32), Buffer.from([1])], destAddr: dest, fee: 2000 });
    cli(`sendrawtransaction ${badTx.toHex()}`);
    console.log('❌ 错误preimage竟然通过');
  } catch (e) {
    badRejected = true;
    console.log('✅ 反例：错误preimage被脚本拒绝（预期）');
  }

  // 正例：正确 preimage 解锁
  const goodTx = spendP2wsh({ utxo, script, value, signer: alice, witnessExtra: [preimage, Buffer.from([1])], destAddr: dest, fee: 2000 });
  const txid = cli(`sendrawtransaction ${goodTx.toHex()}`);
  cli(`generatetoaddress 1 ${dest}`);
  const conf = cliJ(`gettransaction ${txid}`);
  const destAfter = cliJ(`getreceivedbyaddress ${dest}`);
  console.log('✅ 正例：preimage 解锁广播成功:', txid);
  console.log('   确认数:', conf.confirmations, '| 目的地址收款:', destAfter, 'BTC');

  const ok = badRejected && conf.confirmations >= 1 && destAfter >= 1.99;
  console.log('\n' + (ok ? '✅✅✅ 真链 HTLC 验证通过：错误preimage被拒 + 正确preimage解锁到账' : '❌ 有项未通过'));
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('ERR:', e.message); process.exit(1); });
