const AVERAGE = 'average';
const MEDIAN = 'median';
class PerceptualHash
{
	constructor (ctx, size = 64, comparisonMethod = AVERAGE) {
		this.ctx = ctx;
		this.size = size;
		this.comparisonMethod = comparisonMethod;
		this.hash = "";
	}

    generateHash() {
        // Resize the image.
        let resized = this.ctx.getImageData(0, 0, this.size, this.size);

        let matrix = [];
        let row = [];
        let rows = [];
        let col = [];

		// DCT Rows
        for (let y = 0; y < this.size; y++) {
            for (let x = 0; x < this.size; x++) {
				let index = (y*this.size)+x;
				// Grayscale the image as we go
				let rgb = [resized.data[index], resized.data[index+1], resized.data[index+2]];
				row[x] = Math.floor((rgb[0] * 0.2126) + (rgb[1] * 0.7152) + (rgb[2] * 0.0722));
			}
            rows[y] = this.calculateDCT(row);
        }

		// DCT Cols
        for (let x = 0; x < this.size; x++) {
            for (let y = 0; y < this.size; y++)
                col[y] = rows[y][x];
            matrix[x] = this.calculateDCT(col);
        }

        // Extract the top 8x8 pixels.
    	let pixels = [];
        for (let y = 0; y < 8; y++) {
            for (let x = 0; x < 8; x++)
                pixels.push(matrix[y][x]);
        }

		let compare;
        if (this.comparisonMethod === MEDIAN)
            compare = this.median(pixels);
        else
            compare = this.average(pixels);

        // Calculate hash.
        let bits = [];
        for (let pixel of pixels)
            bits.push(pixel > compare ? 1 : 0);

		this.hash = bits.join("");
        return this.hash;
    }

    /**
     * Perform a 1 dimension Discrete Cosine Transformation.
     */
    calculateDCT(matrix)
    {
        let transformed = [];
        let size = matrix.length;

        for (let i = 0; i < size; i++) {
            let sum = 0;
            for (let j = 0; j < size; j++) {
                sum += matrix[j] * Math.cos(i * Math.PI * (j + 0.5) / size);
            }
            sum *= Math.sqrt(2 / size);
            if (i === 0) {
                sum *= 1 / Math.sqrt(2);
            }
            transformed[i] = sum;
        }

        return transformed;
    }

    /**
     * Get the median of the pixel values.
     */
    median(pixels)
    {
        pixels.sort();

        if (pixels.length % 2 === 0) {
            return (pixels[pixels.length / 2 - 1] + pixels[pixels.length / 2]) / 2;
        }

        return pixels[Math.floor(pixels.length / 2)];
    }

    /**
     * Get the average of the pixel values.
     */
    average(pixels)
    {
        // Calculate the average value from top 8x8 pixels, except for the first one.
        let n = pixels.length - 1;

        return pixels.slice(1, n).reduce((sum, a) => sum+a, 0) / n;
    }

	hammingDist(str2) { 
		let i = 0, count = 0; 
		for (let i = 0; i < this.hash.length; i++) 
			if (this.hash[i] != str2[i]) 
				count++; 
		return count; 
	} 
}