#![no_std]
#![no_main]

//! 最小 CKB SPV 验证合约 (里程碑A spike)
//! 验证一个真实 BTC 交易(txid) 存在于比特币链上 —— 依赖 Bitcoin Light Client cell + TransactionProof
//!
//! witness(lock) 布局: btc_txid(32B) || confirmations(4B LE) || tx_proof(rest)
//! CellDep 必须包含 Bitcoin Light Client cell (type = BTC_LC_TYPE_HASH)

use alloc::vec::Vec;
use ckb_std::ckb_constants::Source;
use ckb_std::ckb_types::prelude::*;
use ckb_std::high_level::{load_witness, load_cell_type_hash, load_cell_data, QueryIter};
use ckb_bitcoin_spv_verifier::types::packed::{SpvClient, TransactionProofReader};

ckb_std::default_alloc!();
ckb_std::entry!(program_entry);

/// testnet3 Bitcoin Light Client type hash (来自 RgbppLock config cell)
const BTC_LC_TYPE_HASH: [u8; 32] = [
    0xba,0x9d,0x95,0xde,0x11,0x4a,0x38,0xf4,0x20,0x97,0xb7,0xa3,0xa0,0x6e,0xff,0x2d,
    0x6d,0x66,0x1a,0x77,0x83,0x5a,0x1d,0x13,0xd2,0x5b,0xb8,0x7a,0x3d,0x78,0xc5,0xae,
];

fn program_entry() -> i8 {
    match run() {
        Ok(()) => 0,
        Err(code) => code,
    }
}

fn run() -> Result<(), i8> {
    // 1. 读 witness: txid(32) || confirmations(4 LE) || proof(rest)
    let w = load_witness(0, Source::GroupInput).map_err(|_| 20)?;
    if w.len() < 36 {
        return Err(21);
    }
    let mut txid = [0u8; 32];
    txid.copy_from_slice(&w[0..32]);
    let confirmations = u32::from_le_bytes(w[32..36].try_into().map_err(|_| 22)?);

    // 2. 解析 TransactionProof
    let tx_proof = TransactionProofReader::from_slice(&w[36..]).map_err(|_| 23)?;

    // 3. 在 CellDep 里找 Bitcoin Light Client cell (按 type script hash 匹配)
    let idx = QueryIter::new(load_cell_type_hash, Source::CellDep)
        .enumerate()
        .find_map(|(index, type_hash)| {
            if type_hash.is_some_and(|th| th == &BTC_LC_TYPE_HASH) {
                Some(index)
            } else {
                None
            }
        })
        .ok_or(24)?;

    // 4. 加载 light client 数据并验证交易存在
    let data = load_cell_data(idx, Source::CellDep).map_err(|_| 25)?;
    let client = SpvClient::from_slice(&data).map_err(|_| 26)?;
    client
        .verify_transaction(&txid, tx_proof, confirmations)
        .map_err(|_| 27)?;

    Ok(())
}
