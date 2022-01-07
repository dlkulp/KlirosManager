"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
exports.__esModule = true;
var Jimp = require("jimp");
var fs = require("fs");
compare();
function writeFile(content) {
    try {
        fs.writeFileSync('hashes.txt', content, { flag: "a+" });
        //file written successfully
    }
    catch (err) {
        console.error(err);
    }
}
function compare() {
    return __awaiter(this, void 0, void 0, function () {
        var ourFather, ourFather2, ourFather3, comeWorship, dismissal, ourFatherHash, ourFather3Hash;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, Jimp.read("src/Our Father.png")];
                case 1:
                    ourFather = _a.sent();
                    return [4 /*yield*/, Jimp.read("src/Our Father 2.png")];
                case 2:
                    ourFather2 = _a.sent();
                    return [4 /*yield*/, Jimp.read("src/Our Father 3.png")];
                case 3:
                    ourFather3 = _a.sent();
                    return [4 /*yield*/, Jimp.read("src/come worship.png")];
                case 4:
                    comeWorship = _a.sent();
                    return [4 /*yield*/, Jimp.read("src/dismissal.png")];
                case 5:
                    dismissal = _a.sent();
                    ourFatherHash = ourFather.pHash();
                    ourFather3Hash = ourFather3.pHash();
                    console.log(ourFatherHash);
                    console.log("\n\n");
                    writeFile(ourFatherHash);
                    writeFile("\n");
                    writeFile(ourFather3Hash);
                    writeFile("\n");
                    console.log("Images compared to ourFather\n=========================================");
                    console.log("hash (base 64) ".concat(ourFather.hash(), "\n"));
                    //console.log(`hash (binary)  ${ourFather.hash(2)}\n`);
                    console.log("ourFather2\n=======================");
                    //console.log(`hash (base 64) ${ourFather2.hash()}`);
                    console.log("distance       ".concat(ourFather.distanceFromHash(ourFather2.pHash())));
                    console.log("diff.percent   ".concat(Jimp.diff(ourFather, ourFather2).percent, "\n"));
                    console.log("ourFather3\n=======================");
                    //console.log(`hash (base 64) ${ourFather3.hash()}`);
                    console.log("distance       ".concat(ourFather.distanceFromHash(ourFather3Hash)));
                    console.log("diff.percent   ".concat(Jimp.diff(ourFather, ourFather3).percent, "\n"));
                    console.log("comeWorship\n================");
                    //console.log(`hash (base 64) ${comeWorship.hash()}`);
                    console.log("distance       ".concat(Jimp.distance(ourFather, comeWorship)));
                    console.log("diff.percent   ".concat(Jimp.diff(ourFather, comeWorship).percent, "\n"));
                    console.log("dismissal\n================");
                    //console.log(`hash (base 64) ${dismissal.hash()}`);
                    console.log("distance       ".concat(Jimp.distance(ourFather, dismissal)));
                    console.log("diff.percent   ".concat(Jimp.diff(ourFather, dismissal).percent, "\n"));
                    return [2 /*return*/];
            }
        });
    });
}
