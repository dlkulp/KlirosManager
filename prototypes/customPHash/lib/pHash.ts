import sharp from "sharp";
import {fastDctLee} from "./FastDCT.js";

const SAMPLE_SIZE = 64;
const LOW_SIZE = 8;

export function distance(a: string, b: string) {
	let count = 0;
	for (let i = 0; i < a.length; i++) {
	  if (a[i] !== b[i]) {
		count++;
	  }
	}
	return count;
  };

export async function pHash(image: Buffer, method = "fast") {
	const data = await sharp(image)
	  .greyscale()
	  .resize(SAMPLE_SIZE, SAMPLE_SIZE, { fit: "fill" })
	  .flop()
	  .rotate(-90)
	  .raw()
	  .toBuffer();
	  
	let s: number[][] = convertToMatrix(data);
	  
	//exportImage("preDCT.png", s);
	
	// Apply 2D Fast DCT type II, unscaled - O(n log n)
	if (method == "fast") applyFastDCT(s);
	// Same but not fast - O(n^4)
	else s = applyDCT(s, SAMPLE_SIZE);

	//exportImage("afterDCT.png", s);

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

async function exportImage(fileName: string, arr2d: any[] | Buffer) {
	let uArr: Uint16Array | Buffer | undefined = undefined;
	if (typeof (arr2d as Buffer).buffer === "undefined") {
		let arr = [];
		for (let row of arr2d)
			for (let x of row)
			arr.push(x);
		uArr = Uint16Array.from(arr);
	}
	else  uArr = arr2d as Buffer;
	await sharp(uArr, {raw: {
		width: SAMPLE_SIZE,
		height: SAMPLE_SIZE,
		channels: 1
	  }}).png().toFile(fileName);
}

function applyFastDCT(matrix: Array<Array<number>>) {
	// First dimension
	for (let i = 0; i < SAMPLE_SIZE; i++)
		fastDctLee.transform(matrix[i]);

	matrix = rotateMatrix(matrix);

	// Second dimension
	for (let i = 0; i < SAMPLE_SIZE; i++)
		fastDctLee.transform(matrix[i]);

	matrix = rotateMatrix(matrix);
}

function convertToMatrix(data: Buffer) {
	// convert buffer to 2D array
	let s: Array<Array<number>> = new Array(SAMPLE_SIZE);
	for (let x = 0; x < SAMPLE_SIZE; x++) {
		s[x] = new Array(SAMPLE_SIZE);
		for (let y = 0; y < SAMPLE_SIZE; y++)
			s[x][y] = data[SAMPLE_SIZE * y + x];
	}
	return s;
}

function rotateMatrix(matrix: Array<Array<number>>) {
	let temp:Array<Array<number>> = [];
	// Initialize temp
	for (let j = 0; j < matrix.length; j++)
		temp[j] = [];
	
	// Do rotation
	for (let i = 0; i < matrix.length; i++) 
		for (let j = 0; j < matrix.length; j++)
			temp[j][i] = matrix[i][j];
	return temp;
}

// Old

function initSQRT(N: number) {
	const c = new Array(N);
	for (let i = 1; i < N; i++) {
	  c[i] = 1;
	}
	c[0] = 1 / Math.sqrt(2.0);
	return c;
  }
  
  const SQRT = initSQRT(SAMPLE_SIZE);
  
  function initCOS(N: number) {
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
  
  function applyDCT(f: any[], size: number) {
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