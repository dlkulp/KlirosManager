import { ManipulateImage } from "./imageMagick.js";
import * as fs from "fs";

async function test() {
	let files = [{name:"Our Father", dir:"../src/Our Father.png"}, {name:"Our Father 2", dir:"../src/Our Father 2.png"},{name:"Our Father 3", dir:"../src/Our Father 3.png"}];

	fs.mkdir("out", {recursive:true}, err => {
		if (err) throw err;
	});
	await ManipulateImage.init();
	for (let file of files) {
		fs.mkdir(`out/${file.name}`, {recursive:true}, err => {
			if (err) throw err;
		});
		let img = new ManipulateImage(fs.readFileSync(file.dir));
		img.rotate(180).export(`out/${file.name}/rotate.png`, "png");
		img.grayscale().export(`out/${file.name}/grayscale.png`,"png");
		img.deskew().export(`out/${file.name}/deskew.png`,"png");
		img.trim().export(`out/${file.name}/trim.png`,"png");
		img.resize(128, 128).export(`out/${file.name}/resize.png`, "png");
		img.rotate(180).grayscale().deskew(60).trim(50).resize(128, 128).export(`out/${file.name}/combined.jpg`, "jpeg");
	}

	console.log("success!");
}

test();