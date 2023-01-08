import * as fs from "fs";
import { pHash, distance } from "./lib/pHash.js";
compare();
function clearFile() {
    try {
        fs.writeFileSync('hashes.txt', "");
        //file written successfully
    }
    catch (err) {
        console.error(err);
    }
}
function writeFile(content) {
    try {
        fs.writeFileSync('hashes.txt', content, { flag: "a+" });
        //file written successfully
    }
    catch (err) {
        console.error(err);
    }
}
function percentDifference(a, b) {
    return distance(a, b) / a.length;
}
async function compare() {
    const hashMethod = "slow";
    clearFile();
    let files = [{ name: "Our Father 2", dir: "../src/Our Father 2.png" }, { name: "Our Father 3", dir: "../src/Our Father 3.png" }, { name: "O Come Let Us Worship", dir: "../src/come worship.png" }, { name: "Dismissal", dir: "../src/dismissal.png" }];
    let ourFatherHash = await pHash(fs.readFileSync("../src/Our Father.png"), hashMethod);
    console.log(ourFatherHash);
    // writeFile(ourFatherHash);
    // writeFile("\n");
    // for (let file of files) {
    // 	const src = fs.readFileSync(file.dir);
    // 	let fileHash = await pHash(src, hashMethod);
    // 	writeFile(fileHash);
    // 	writeFile("\n");
    // 	console.log(`\n${file.name}\n=======================`);
    // 	console.log(`distance    ${distance(ourFatherHash, fileHash)}`);
    // 	console.log(`percent     ${Math.round(percentDifference(ourFatherHash, fileHash) * 100)}%`);
    // }
}
