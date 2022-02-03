<template>
<div :class="`card overflow-hidden ${cardStyle} ${baseTextColor ? 'text-white' : ''}`">
	<slot name="header" />
	<div v-if="imageURL" class="card-img-top"><img class="img-fluid" :src="imageURL" :alt="title" /></div>
	<div :class="bodyStyle">
		<div v-if="textOverlay">
			<div v-if="titleSize == `sm`" :class="`card-title ${baseTextColor ? 'text-white' : ''}`">
				{{ title }}
			</div>
			<h3 :class="baseTextColor ? 'text-white' : ''" v-if="titleSize == `lg`">{{ title }}</h3>
			<h5 :class="baseTextColor ? 'text-white' : ''" v-if="titleSize == `default`">{{ title }}</h5>
			<slot />
		</div>
		<template v-else>
			<div v-if="titleSize == `sm`" :class="`card-title ${baseTextColor ? 'text-white' : ''}`">
				{{ title }}
			</div>
			<h3 :class="baseTextColor ? 'text-white' : ''" v-if="titleSize == `lg`">{{ title }}</h3>
			<h5 :class="baseTextColor ? 'text-white' : ''" v-if="titleSize == `default`">{{ title }}</h5>
			<slot />
		</template>
	</div>
	<slot name="footer" />
</div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, toRefs } from "vue";

export default defineComponent({
	props: {
		title: {type: String, default: ""},
		titleSize: {type: String, default: "default", validator(t: string) {return ["default", "lg", "sm"].indexOf(t) !== -1}},
		background: {type: String, default: "light", validator(b: string) {return ["primary", "secondary", "success", "info", "warning", "danger", "light", "dark"].indexOf(b) !== -1}},
		imageURL: {type: String},
		textOverlay: {type: Boolean, default: false},
		textColor: {type: String, default: "", validator(t:string) {return ["dark", "light", ""].indexOf(t) !== -1}}
	},
	setup(props: Props) {
		const { textColor, imageURL, textOverlay, background } = toRefs(props);
		const cardStyle = ref(""), bodyStyle = ref(`card-body bg-${background.value}`);
		const baseTextColor = ref("");

		onMounted(async () => {
			if (textOverlay.value) {
				if (imageURL?.value && !textColor.value)
					baseTextColor.value = await isItDark(imageURL.value) ? "light" : "dark";
				else if (textColor.value)
					baseTextColor.value = textColor.value;

				cardStyle.value = baseTextColor.value == "light" ? "bg-dark light" : "bg-light dark";
				bodyStyle.value = "card-img-overlay d-flex align-items-end";
			}
		});

		return { bodyStyle, cardStyle, baseTextColor }
	}
});

// https://stackoverflow.com/a/13766539/2525751
function isItDark(imageSrc: string) {
        let fuzzy = 0.1;
		let img: HTMLImageElement = document.createElement("img") as HTMLImageElement;
        img.src = imageSrc;
		img.style.display = "none";
		document.body.appendChild(img);

		return new Promise<Boolean>((resolve, reject) => {
			img.onerror = reject;
			img.onload = () => {
				// create canvas
				let canvas = document.createElement("canvas");
				canvas.width = img.width;
				canvas.height = img.height;

				let ctx = canvas.getContext("2d");
				if (!ctx) return false;

				ctx.drawImage(img,0,0);

				let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
				let data = imageData.data;
				let r,g,b, max_rgb;
				let light = 0, dark = 0;

				for(let x = 0, len = data.length; x < len; x += 4) {
					r = data[x];
					g = data[x+1];
					b = data[x+2];

					max_rgb = Math.max(Math.max(r, g), b);
					if (max_rgb < 128)
						dark++;
					else
						light++;
				}

				let dl_diff = ((light - dark) / (img.width * img.height));
				// true == dark, false == light
				resolve((dl_diff + fuzzy < 0) ? true : false);
			}
		});
    }

interface Props {
	title: string;
	titleSize: string;
	background: string;
	imageURL?: string;
	textOverlay: boolean;
	textColor: string;
}
</script>