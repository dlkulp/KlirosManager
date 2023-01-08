import sharp from "sharp";
import { fastDctLee } from "./FastDCT.js";
const SAMPLE_SIZE = 64;
const LOW_SIZE = 8;
export function distance(a, b) {
    let count = 0;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) {
            count++;
        }
    }
    return count;
}
;
export async function pHash(image, method = "fast") {
    const data = await sharp(image)
        .greyscale()
        .resize(SAMPLE_SIZE, SAMPLE_SIZE, { fit: "fill" })
        .rotate()
        .raw()
        .toBuffer();
    // copy signal
    let s = new Array(SAMPLE_SIZE);
    for (let x = 0; x < SAMPLE_SIZE; x++) {
        s[x] = new Array(SAMPLE_SIZE);
        for (let y = 0; y < SAMPLE_SIZE; y++) {
            s[x][y] = data[SAMPLE_SIZE * y + x];
        }
    }
    try {
        //exportImage('preDCT.png', data);
        exportImage("signal.png", s);
        //file written successfully
    }
    catch (err) {
        console.error(err);
    }
    // Apply DCT type II, unscaled
    if (method == "fast")
        applyFastDCT(s);
    // apply 2D DCT II
    else
        s = applyDCT(s, SAMPLE_SIZE);
    try {
        exportImage('afterDCT.png', s);
        //file written successfully
    }
    catch (err) {
        console.error(err);
    }
    // get AVG on high frequencies
    let totalSum = 0;
    for (let x = 0; x < LOW_SIZE; x++) {
        for (let y = 0; y < LOW_SIZE; y++) {
            totalSum += s[x + 1][y + 1];
        }
    }
    const avg = totalSum / (LOW_SIZE * LOW_SIZE);
    // compute hash
    let fingerprint = "";
    for (let x = 0; x < LOW_SIZE; x++) {
        for (let y = 0; y < LOW_SIZE; y++) {
            fingerprint += s[x + 1][y + 1] > avg ? "1" : "0";
        }
    }
    return fingerprint;
}
async function exportImage(fileName, arr) {
    await sharp(Uint16Array.from(arr), { raw: {
            width: SAMPLE_SIZE,
            height: SAMPLE_SIZE,
            channels: 1
        } }).png().toFile(fileName);
}
function applyFastDCT(matrix) {
    // First dimension
    for (let layer of matrix)
        fastDctLee.transform(layer);
    // Rotate matrix
    rotateMatrix(matrix);
    // Second dimension
    for (let layer of matrix)
        fastDctLee.transform(layer);
}
function rotateMatrix(matrix) {
    for (let i = 0; i < matrix.length; i++) {
        for (let j = 0; j < matrix.length; j++) {
            const temp = matrix[i][j];
            matrix[i][j] = matrix[j][i];
            matrix[j][i] = temp;
        }
    }
}
// Old
function initSQRT(N) {
    const c = new Array(N);
    for (let i = 1; i < N; i++) {
        c[i] = 1;
    }
    c[0] = 1 / Math.sqrt(2.0);
    return c;
}
const SQRT = initSQRT(SAMPLE_SIZE);
function initCOS(N) {
    const cosines = new Array(N);
    for (let k = 0; k < N; k++) {
        cosines[k] = new Array(N);
        for (let n = 0; n < N; n++) {
            cosines[k][n] = Math.cos(((2 * k + 1) / (2.0 * N)) * n * Math.PI);
        }
    }
    return cosines;
}
const COS = initCOS(SAMPLE_SIZE);
function applyDCT(f, size) {
    var N = size;
    var F = new Array(N);
    for (var u = 0; u < N; u++) {
        F[u] = new Array(N);
        for (var v = 0; v < N; v++) {
            var sum = 0;
            for (var i = 0; i < N; i++) {
                for (var j = 0; j < N; j++) {
                    sum += COS[i][u] * COS[j][v] * f[i][j];
                }
            }
            sum *= (SQRT[u] * SQRT[v]) / 4;
            F[u][v] = sum;
        }
    }
    return F;
}
