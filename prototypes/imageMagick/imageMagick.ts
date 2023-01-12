import { ColorSpace, initializeImageMagick } from "@imagemagick/magick-wasm";
import { ImageMagick, MagickFormat, IMagickImage, Percentage } from "@imagemagick/magick-wasm";
import * as fs from "fs";

export class ManipulateImage {
	img: Buffer;
	imgArr!: Uint8Array;

	private stack: Function[];

	// Initialize by calling "await ImageMagic.init()"
	constructor(img: Buffer) {
		this.img = img;
		this.stack = [];
	}

	static async init() {
		await initializeImageMagick();
	}

	// Trim
	private _trim(image: IMagickImage, fuzzPercent = 10) {
		image.colorFuzz = new Percentage(fuzzPercent);
		image.trim();
	}
	public trim(fuzzPercent = 10) {
		this.stack.push((image: IMagickImage) => this._trim(image, fuzzPercent));
		return this;
	}

	// Resize
	private _resize(image: IMagickImage, height: number, width: number) {
		image.resize(width, height);
	}
	public resize(height: number, width: number) {
		this.stack.push((image: IMagickImage) => this._resize(image, height, width));
		return this;
	}

	// Rotate
	private _rotate(image: IMagickImage, degrees = 90 ) {
		image.rotate(degrees);
	}
	public rotate(degrees = 90) {
		this.stack.push((image: IMagickImage) => this._rotate(image, degrees));
		return this;
	}

	// Greyscale
	private _grayscale(image: IMagickImage) {
		image.colorSpace = ColorSpace.Gray;
	}
	public grayscale() {
		this.stack.push((image: IMagickImage) => this._grayscale(image));
		return this;
	}

	// Deskew
	private _deskew(image: IMagickImage, threshold = 40) {
		image.deskew(new Percentage(threshold));
	}
	public deskew(threshold = 40) {
		this.stack.push((image: IMagickImage) => this._deskew(image, threshold));
		return this;
	}

	// Write
	public export(name: string = "testImage", _format:string = "Jpeg") {
		let format = _format.replace(/^\w/, c => c.toUpperCase());
		if (typeof MagickFormat[format as keyof typeof MagickFormat] == "undefined")
			console.error("Unknown filetype.");
		else {
			this.imgArr = new Uint8Array(this.img);
			ImageMagick.read(this.imgArr, image => {
				for (let command of this.stack)
					command(image);
				image.write((content: Uint8Array) => fs.writeFileSync(name, content), MagickFormat[format as keyof typeof MagickFormat]);
			});
			this.stack = [];
		}
	}

	public async toUint8Array() {
		let ret: Uint8Array;
		this.imgArr = new Uint8Array(this.img);
		ret = await new Promise((resolve, _reject) => {
			ImageMagick.read(this.imgArr, image => {
				for (let command of this.stack)
					command(image);
				image.write((content: Uint8Array) => resolve(content));
			})
		});
		this.stack = [];
		return ret;
	}
}