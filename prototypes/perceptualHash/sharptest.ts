
import {pHash} from "./pHash.js";
import * as fs from "fs";

compare();
function clearFile() {
	try {
        fs.writeFileSync('hashes.txt', "");
        //file written successfully
    } catch (err) {
        console.error(err);
    }
}
function writeFile(content: string) {
    try {
        fs.writeFileSync('hashes.txt', content, {flag: "a+"});
        //file written successfully
    } catch (err) {
        console.error(err);
    }
}

function percentDifference(a: string, b: string) {
	return pHash.getDist(a, b) / 64;
}

async function compare()
{
	clearFile()
	let files = [{name:"Our Father 2", dir:"../src/Our Father 2.png"},{name:"Our Father 3", dir:"../src/Our Father 3.png"},{name:"O Come Let Us Worship", dir:"../src/come worship.png"},{name:"Dismissal", dir:"../src/dismissal.png"}];
	
	let ourFatherHash = await pHash.getHash(fs.readFileSync("../src/Our Father.png"));
	for (let file of files) {
		const src = fs.readFileSync(file.dir);
		let fileHash = await pHash.getHash(src);
		writeFile(fileHash);
		writeFile("\n");
		console.log(`\n${file.name}\n=======================`);
		console.log(`distance    ${pHash.getDist(ourFatherHash,fileHash)}`);
		console.log(`percent     ${Math.round(percentDifference(ourFatherHash, fileHash) * 100)}%`);
	}
}