#![no_std]
#![no_main]

//! CKB HTLC Lock Script
//! args    = hash(32B) || timelock(8B, LE u64)
//! witness = WitnessArgs.lock 字段填 preimage(32B)，或留空
//!
//! 通过条件（满足其一）：
//!   A) hashlock: 某个 group input 的 witness.lock 是 32B preimage 且 sha256(preimage) == hash
//!   B) timelock: 所有 group input 的 since 均为「绝对高度」且 >= timelock

use alloc::vec::Vec;

use ckb_std::ckb_constants::Source;
use ckb_std::ckb_types::prelude::*;
use ckb_std::error::SysError;
use ckb_std::high_level::{load_input_since, load_script, load_witness};
use sha2::{Digest, Sha256};

ckb_std::default_alloc!();
ckb_std::entry!(program_entry);

const ARGS_LEN: usize = 40;
const PREIMAGE_LEN: usize = 32;

fn program_entry() -> i8 {
    match run() {
        Ok(()) => 0,
        Err(code) => code,
    }
}

fn run() -> Result<(), i8> {
    let script = load_script().map_err(|_| 10i8)?;
    let args = script.args().raw_data();
    if args.len() != ARGS_LEN {
        return Err(11);
    }
    let mut expected = [0u8; 32];
    expected.copy_from_slice(&args[0..32]);
    let mut tl = [0u8; 8];
    tl.copy_from_slice(&args[32..40]);
    let timelock = u64::from_le_bytes(tl);

    // ---------- A) hashlock 分支 ----------
    let mut i: usize = 0;
    loop {
        match load_witness(i, Source::GroupInput) {
            Ok(preimage) => {
                if preimage.len() == PREIMAGE_LEN {
                    let h = Sha256::digest(preimage.as_slice());
                    if h.as_slice() == expected {
                        return Ok(());
                    }
                }
                i += 1;
            }
            Err(SysError::IndexOutOfBound) => break,
            Err(_) => return Err(13),
        }
    }

    // ---------- B) timelock 分支 ----------
    let mut j: usize = 0;
    loop {
        match load_input_since(j, Source::GroupInput) {
            Ok(since) => {
                // 必须是绝对高度锁：bit63=相对标志(须0)，bit62=时间标志(须0)
                if since & (1u64 << 63) != 0 {
                    return Err(14);
                }
                if since & (1u64 << 62) != 0 {
                    return Err(15);
                }
                if since < timelock {
                    return Err(16);
                }
                j += 1;
            }
            Err(SysError::IndexOutOfBound) => break,
            Err(_) => return Err(17),
        }
    }
    if j == 0 {
        return Err(18);
    }

    Ok(())
}
