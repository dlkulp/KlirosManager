"use strict";
exports.__esModule = true;
exports.pHash = void 0;
var _pHash = require("sharp-phash");
var _distance = require("sharp-phash/distance");
var pHash = /** @class */ (function () {
    function pHash() {
    }
    pHash.getHash = function (img) {
        //@ts-ignore - seems to be really confused about what this module is. This works....
        return _pHash(img);
    };
    pHash.getDist = function (a, b) {
        //@ts-ignore - also confused about this one. Not sure how to make it work other than just tell TS to shutup because it works
        return _distance(a, b);
    };
    return pHash;
}());
exports.pHash = pHash;
