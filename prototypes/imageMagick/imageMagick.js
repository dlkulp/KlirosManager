"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ManipulateImage = void 0;
const magick_wasm_1 = require("@imagemagick/magick-wasm");
const magick_wasm_2 = require("@imagemagick/magick-wasm");
const fs = __importStar(require("fs"));
class ManipulateImage {
    img;
    imgArr;
    stack;
    // Initialize by calling "await ImageMagic.init()"
    constructor(img) {
        this.img = img;
        this.stack = [];
    }
    static async init() {
        await (0, magick_wasm_1.initializeImageMagick)();
    }
    // Trim
    _trim(image, fuzzPercent = 10) {
        image.colorFuzz = new magick_wasm_2.Percentage(fuzzPercent);
        image.trim();
    }
    trim(fuzzPercent = 10) {
        this.stack.push((image) => this._trim(image, fuzzPercent));
        return this;
    }
    // Resize
    _resize(image, height, width) {
        image.resize(width, height);
    }
    resize(height, width) {
        this.stack.push((image) => this._resize(image, height, width));
        return this;
    }
    // Rotate
    _rotate(image, degrees = 90) {
        image.rotate(degrees);
    }
    rotate(degrees = 90) {
        this.stack.push((image) => this._rotate(image, degrees));
        return this;
    }
    // Greyscale
    _grayscale(image) {
        image.colorSpace = magick_wasm_1.ColorSpace.Gray;
    }
    grayscale() {
        this.stack.push((image) => this._grayscale(image));
        return this;
    }
    // Deskew
    _deskew(image, threshold = 40) {
        image.deskew(new magick_wasm_2.Percentage(threshold));
    }
    deskew(threshold = 40) {
        this.stack.push((image) => this._deskew(image, threshold));
        return this;
    }
    // Write
    export(name = "testImage", _format = "Jpeg") {
        let format = _format.replace(/^\w/, c => c.toUpperCase());
        if (typeof magick_wasm_2.MagickFormat[format] == "undefined")
            console.error("Unknown filetype.");
        else {
            this.imgArr = new Uint8Array(this.img);
            magick_wasm_2.ImageMagick.read(this.imgArr, image => {
                for (let command of this.stack)
                    command(image);
                image.write((content) => fs.writeFileSync(name, content), magick_wasm_2.MagickFormat[format]);
            });
            this.stack = [];
        }
    }
    async toUint8Array() {
        let ret;
        this.imgArr = new Uint8Array(this.img);
        ret = await new Promise((resolve, _reject) => {
            magick_wasm_2.ImageMagick.read(this.imgArr, image => {
                for (let command of this.stack)
                    command(image);
                image.write((content) => resolve(content));
            });
        });
        this.stack = [];
        return ret;
    }
}
exports.ManipulateImage = ManipulateImage;
//# sourceMappingURL=imageMagick.js.map