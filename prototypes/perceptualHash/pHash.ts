import * as _pHash from "sharp-phash";
import * as _distance from "sharp-phash/distance";

export class pHash {
	public static getHash(img: Buffer): Promise<string> {
		//@ts-ignore - seems to be really confused about what this module is. This works....
		return _pHash(img);
	}
	public static getDist(a: string, b: string): number {
		//@ts-ignore - also confused about this one. Not sure how to make it work other than just tell TS to shutup because it works
		return _distance(a, b);
	}
}