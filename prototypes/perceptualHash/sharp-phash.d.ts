declare module "sharp-phash" {
	function phash(img: Buffer): Promise<string>;
	export default phash;
}
declare module "sharp-phash/distance" {
	function distance(a: string, b: string): number;
	export default distance;
}