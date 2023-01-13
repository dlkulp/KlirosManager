import { ColorSpace, initializeImageMagick } from "@imagemagick/magick-wasm";
import { ImageMagick, MagickFormat, IMagickImage, Percentage, MagickGeometry } from "@imagemagick/magick-wasm";
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
		image.resize(new MagickGeometry(`${width}x${height}!`));
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
	public export(name: string = "image.jpeg") {
		let _format = name.split(".").at(-1) || "jpeg";
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
				
				// Bmp is an uncompressed, quad-channel format, for this usage we need one value only so we convert to a single channel
				// More here: https://www.imagemagick.org/Usage/color_mods/
				function convert(content: Uint8Array) {
					let px = image.height * image.width;
					let out = new Uint8Array(px);
					for (let x = 0, r = 0, g = 1, b = 2, a = 3; x < px; x++, r+=4, g+=4, b+=4, a+=4)
						out[x] = (content[r]*.2)+(content[g]*.5)+(content[b]*.3);
					return out;
				}
				
				image.write((content: Uint8Array) => resolve(convert(content)), MagickFormat.Bmp);
			})
		});
		this.stack = [];
		return ret;
	}
}