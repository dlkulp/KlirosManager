import * as Jimp from "jimp";
import * as fs from "fs";


interface JIMP extends Jimp {
    pHash(): string;
}

compare();
function writeFile(content: string) {
    try {
        fs.writeFileSync('hashes.txt', content, {flag: "a+"});
        //file written successfully
    } catch (err) {
        console.error(err);
    }
}

async function compare()
{
    const ourFather = await Jimp.read("src/Our Father.png") as JIMP;
    const ourFather2 = await Jimp.read("src/Our Father 2.png") as JIMP;
    const ourFather3 = await Jimp.read("src/Our Father 3.png") as JIMP;
    const comeWorship = await Jimp.read("src/come worship.png") as JIMP;
    const dismissal = await Jimp.read("src/dismissal.png") as JIMP;
    
    let ourFatherHash = ourFather.pHash();
    let ourFather3Hash = ourFather3.pHash();
    console.log(ourFatherHash);
    console.log(`\n\n`);

    writeFile(ourFatherHash);
    writeFile("\n");
    writeFile(ourFather3Hash);
    writeFile("\n");

    console.log("Images compared to ourFather\n=========================================");
    console.log(`hash (base 64) ${ourFather.hash()}\n`);
    //console.log(`hash (binary)  ${ourFather.hash(2)}\n`);

    console.log("ourFather2\n=======================");
    //console.log(`hash (base 64) ${ourFather2.hash()}`);
    console.log(`distance       ${ourFather.distanceFromHash(ourFather2.pHash())}`);
    console.log(`diff.percent   ${Jimp.diff(ourFather, ourFather2).percent}\n`);

    console.log("ourFather3\n=======================");
    //console.log(`hash (base 64) ${ourFather3.hash()}`);
    console.log(`distance       ${ourFather.distanceFromHash(ourFather3Hash)}`);
    console.log(`diff.percent   ${Jimp.diff(ourFather, ourFather3).percent}\n`);

    console.log("comeWorship\n================");
    //console.log(`hash (base 64) ${comeWorship.hash()}`);
    console.log(`distance       ${Jimp.distance(ourFather, comeWorship)}`);
    console.log(`diff.percent   ${Jimp.diff(ourFather, comeWorship).percent}\n`);
    
    console.log("dismissal\n================");
    //console.log(`hash (base 64) ${dismissal.hash()}`);
    console.log(`distance       ${Jimp.distance(ourFather, dismissal)}`);
    console.log(`diff.percent   ${Jimp.diff(ourFather, dismissal).percent}\n`);
}