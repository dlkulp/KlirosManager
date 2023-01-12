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
const imageMagick_js_1 = require("./imageMagick.js");
const fs = __importStar(require("fs"));
async function test() {
    let files = [{ name: "Our Father", dir: "../src/Our Father.png" }, { name: "Our Father 2", dir: "../src/Our Father 2.png" }, { name: "Our Father 3", dir: "../src/Our Father 3.png" }];
    fs.mkdir("out", { recursive: true }, err => {
        if (err)
            throw err;
    });
    await imageMagick_js_1.ManipulateImage.init();
    for (let file of files) {
        fs.mkdir(`out/${file.name}`, { recursive: true }, err => {
            if (err)
                throw err;
        });
        let img = new imageMagick_js_1.ManipulateImage(fs.readFileSync(file.dir));
        img.rotate(180).export(`out/${file.name}/rotate.png`, "png");
        img.grayscale().export(`out/${file.name}/grayscale.png`, "png");
        img.deskew().export(`out/${file.name}/deskew.png`, "png");
        img.trim().export(`out/${file.name}/trim.png`, "png");
        img.resize(128, 128).export(`out/${file.name}/resize.png`, "png");
        img.rotate(180).grayscale().deskew(60).trim(50).resize(128, 128).export(`out/${file.name}/combined.jpg`, "jpeg");
    }
    console.log("success!");
}
test();
//# sourceMappingURL=imageTest.js.map