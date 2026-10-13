/**
 * Steam TOTP & maFile Parser
 * Pure JavaScript implementation of Steam Guard 2FA code generation
 * Works offline & in-browser via Web Crypto API with SHA-1 HMAC fallback.
 */

(function (global) {
  'use strict';

  const STEAM_CHARS = '23456789BCDFGHJKMNPQRTVWXY';

  // Base64 helper with strict/safe padding
  function base64ToUint8(b64) {
    if (!b64 || typeof b64 !== 'string') return new Uint8Array(0);
    let clean = b64.trim().replace(/\s+/g, '');
    const pad = clean.length % 4;
    if (pad) {
      clean += '='.repeat(4 - pad);
    }
    const bin = atob(clean);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) {
      arr[i] = bin.charCodeAt(i);
    }
    return arr;
  }

  // 64-bit big-endian time buffer (struct.pack('>Q', step))
  function getTimeBuffer(step) {
    const buf = new ArrayBuffer(8);
    const view = new DataView(buf);
    view.setUint32(0, Math.floor(step / 0x100000000), false);
    view.setUint32(4, step >>> 0, false);
    return new Uint8Array(buf);
  }

  // Pure JS fallback SHA-1 HMAC in case Web Crypto is unavailable
  function jsSha1Hmac(keyBytes, msgBytes) {
    function rotl(n, s) {
      return (n << s) | (n >>> (32 - s));
    }

    function sha1Block(H, W) {
      let a = H[0], b = H[1], c = H[2], d = H[3], e = H[4];
      for (let i = 0; i < 80; i++) {
        let f, k;
        if (i < 20) {
          f = (b & c) | (~b & d);
          k = 0x5a827999;
        } else if (i < 40) {
          f = b ^ c ^ d;
          k = 0x6ed9eba1;
        } else if (i < 60) {
          f = (b & c) | (b & d) | (c & d);
          k = 0x8f1bbcdc;
        } else {
          f = b ^ c ^ d;
          k = 0xca62c1d6;
        }
        const temp = (rotl(a, 5) + f + e + k + W[i]) >>> 0;
        e = d;
        d = c;
        c = rotl(b, 30);
        b = a;
        a = temp;
      }
      H[0] = (H[0] + a) >>> 0;
      H[1] = (H[1] + b) >>> 0;
      H[2] = (H[2] + c) >>> 0;
      H[3] = (H[3] + d) >>> 0;
      H[4] = (H[4] + e) >>> 0;
    }

    function sha1(data) {
      const bitLen = data.length * 8;
      const padLen = (((data.length + 8) >> 6) + 1) << 6;
      const buf = new Uint8Array(padLen);
      buf.set(data);
      buf[data.length] = 0x80;
      const view = new DataView(buf.buffer);
      view.setUint32(padLen - 4, bitLen >>> 0, false);
      view.setUint32(padLen - 8, Math.floor(bitLen / 0x100000000), false);

      const H = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0];
      const W = new Uint32Array(80);

      for (let i = 0; i < padLen; i += 64) {
        for (let t = 0; t < 16; t++) {
          W[t] = view.getUint32(i + t * 4, false);
        }
        for (let t = 16; t < 80; t++) {
          W[t] = rotl(W[t - 3] ^ W[t - 8] ^ W[t - 14] ^ W[t - 16], 1);
        }
        sha1Block(H, W);
      }

      const out = new Uint8Array(20);
      const outView = new DataView(out.buffer);
      for (let i = 0; i < 5; i++) {
        outView.setUint32(i * 4, H[i], false);
      }
      return out;
    }

    // HMAC preparation: block size 64 bytes
    const blockSize = 64;
    let key = keyBytes;
    if (key.length > blockSize) {
      key = sha1(key);
    }
    const kPad = new Uint8Array(blockSize);
    kPad.set(key);

    const oPad = new Uint8Array(blockSize);
    const iPad = new Uint8Array(blockSize);
    for (let i = 0; i < blockSize; i++) {
      oPad[i] = kPad[i] ^ 0x5c;
      iPad[i] = kPad[i] ^ 0x36;
    }

    const inner = new Uint8Array(blockSize + msgBytes.length);
    inner.set(iPad);
    inner.set(msgBytes, blockSize);
    const innerHash = sha1(inner);

    const outer = new Uint8Array(blockSize + innerHash.length);
    outer.set(oPad);
    outer.set(innerHash, blockSize);
    return sha1(outer);
  }

  function extractCodeFromHmac(hmacBytes) {
    const begin = hmacBytes[19] & 0x0f;
    const view = new DataView(hmacBytes.buffer, hmacBytes.byteOffset + begin, 4);
    let fullCode = view.getUint32(0, false) & 0x7fffffff;
    let code = '';
    for (let i = 0; i < 5; i++) {
      const rem = fullCode % STEAM_CHARS.length;
      fullCode = Math.floor(fullCode / STEAM_CHARS.length);
      code += STEAM_CHARS[rem];
    }
    return code;
  }

  async function generateSteamGuardCode(sharedSecret, timestampSec = null) {
    if (!sharedSecret) return '-----';
    const ts = timestampSec !== null ? timestampSec : Math.floor(Date.now() / 1000);
    const timeStep = Math.floor(ts / 30);
    const keyBytes = base64ToUint8(sharedSecret);
    const msgBytes = getTimeBuffer(timeStep);

    // Try Web Crypto API first
    if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
      try {
        const cryptoKey = await window.crypto.subtle.importKey(
          'raw',
          keyBytes,
          { name: 'HMAC', hash: { name: 'SHA-1' } },
          false,
          ['sign']
        );
        const sig = await window.crypto.subtle.sign('HMAC', cryptoKey, msgBytes);
        return extractCodeFromHmac(new Uint8Array(sig));
      } catch (e) {
        // Fallback to pure JS if SubtleCrypto fails
      }
    }

    // Pure JS HMAC-SHA1 fallback
    const hmacResult = jsSha1Hmac(keyBytes, msgBytes);
    return extractCodeFromHmac(hmacResult);
  }

  function getSecondsRemaining(timestampSec = null) {
    const ts = timestampSec !== null ? timestampSec : Math.floor(Date.now() / 1000);
    return 30 - (ts % 30);
  }

  function parseMaFile(fileContent, fileName = '') {
    const trimmed = fileContent.trim();
    let data;
    try {
      data = JSON.parse(trimmed);
    } catch (e) {
      throw new Error('Файл повреждён или зашифрован. Требуется незашифрованный .maFile.');
    }

    if (!data || typeof data !== 'object') {
      throw new Error('Некорректный формат maFile (ожидался JSON объект).');
    }

    const sharedSecret = data.shared_secret || data.sharedSecret;
    if (!sharedSecret) {
      throw new Error('В файле отсутствует поле "shared_secret". Генерация кода невозможна.');
    }

    const accountName = data.account_name || data.accountName || fileName.replace(/\.mafile$/i, '') || 'Steam Account';
    const steamId = (data.Session && data.Session.SteamID) || data.steamid || data.SteamId || data.steam_id || '';
    const identitySecret = data.identity_secret || data.identitySecret || '';
    const revocationCode = data.revocation_code || '';

    return {
      id: `${accountName}_${steamId || Date.now()}`,
      accountName,
      steamId: String(steamId),
      sharedSecret,
      identitySecret,
      revocationCode,
      raw: data,
    };
  }

  // Export
  const SteamTOTP = {
    generateCode: generateSteamGuardCode,
    getSecondsRemaining,
    parseMaFile,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = SteamTOTP;
  } else {
    global.SteamTOTP = SteamTOTP;
  }
})(typeof window !== 'undefined' ? window : this);
