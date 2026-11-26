use core::result::Result;
use ckb_std::ckb_constants::Source;
use ckb_std::ckb_types::bytes::Bytes;
use ckb_std::ckb_types::prelude::*;
use ckb_std::high_level::{load_script, load_transaction, load_witness_args};
use sha2::{Digest, Sha256};
use crate::error::Error;

const HASH_LEN: usize = 32;
const TIMELOCK_LEN: usize = 8;

pub fn main() -> Result<(), Error> {
    let script = load_script()?;
    let args: Bytes = script.args().unpack();
    let a = args.as_ref();
    if a.len() != HASH_LEN + TIMELOCK_LEN { return Err(Error::Encoding); }
    let hash = &a[..HASH_LEN];
    let mut tl = [0u8; TIMELOCK_LEN];
    tl.copy_from_slice(&a[HASH_LEN..HASH_LEN + TIMELOCK_LEN]);
    let timelock = u64::from_le_bytes(tl);

    let wa = load_witness_args(0, Source::GroupInput)?;
    let lock = match wa.lock().to_opt() { Some(b) => b.unpack(), None => Bytes::new() };
    let w = lock.as_ref();

    if w.len() == HASH_LEN {
        let mut h = Sha256::new();
        h.update(w);
        let d = h.finalize();
        if d.as_slice() == hash { return Ok(()); }
        return Err(Error::MyError);
    }

    let tx = load_transaction()?;
    let since: u64 = tx.raw().inputs().get(0).map(|i| i.since().unpack()).unwrap_or(0);
    if since >= timelock { return Ok(()); }
    Err(Error::MyError)
}
