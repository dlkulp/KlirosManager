import Tooltip from "bootstrap/js/dist/tooltip.js";

const defaultConfig = {
	placement: "top",
	title: "",
	variant: "dark",
	trigger: "hover",
	html: false
}

const validPlacements = {top:true,topleft:true,topright:true,right:true,righttop:true,rightbottom:true,bottom:true,bottomleft:true,bottomright:true,left:true,lefttop:true,leftbottom:true};
const validVariants = {primary:true,secondary:true,success:true,danger:true,warning:true,info:true,light:true,dark:true,default:true};
const validTriggers = {focus:true,hover:true,click:true,blur:true,manual:true};

function getDefinedBoolean(values: string[]|boolean[]) {
	if (values.length == 0) return;
	let ret: boolean | undefined;
	for (let value of values) {
		if (typeof value === "string")
			value = Boolean(value);
		else if (typeof value === "undefined")
			continue;
		else if (typeof value !== "boolean")
			continue;
		ret = value;
		break;
	}
	return ret;
}

// Usage <element v-kd-tooltip="{title: 'example', placement: 'top', variant: 'dark', html: false}"></element>
export default {
	dName: "kdTooltip",
	dInit: (el: HTMLElement, binding: {value: any}) => {
		// Handle custom variant option
		let variant = el.dataset.ftVariant || binding.value?.variant || defaultConfig.variant;
		if (variant == "default")
			variant = "dark";
		if (!(<any>validVariants)[variant]) {
			console.warn(`Unknown tooltip variant: ${variant}`);
			variant = defaultConfig.variant;
		}

		// Consolidate options
		let config = {
			placement: el.dataset.ftPlacement || binding.value?.placement || defaultConfig.placement,
			title: el.getAttribute("title") || binding.value?.title || defaultConfig.title,
			customClass: `ft-${variant}`,
			trigger: el.dataset.ftTrigger || binding.value?.trigger || defaultConfig.trigger,
			html: getDefinedBoolean([el.dataset.ftHtml, binding.value?.html, defaultConfig.html])
		};

		// Warn for unknown option values
		if (!(<any>validPlacements)[config.placement]) {
			console.warn(`Unknown tooltip placement: ${config.placement}`);
			config.placement = defaultConfig.placement;
		}
		if (config.trigger.split(" ").find((trigger: any) => !(<any>validTriggers)[trigger])) {
			console.warn(`Unknown tooltip trigger: ${config.trigger}`);
			config.trigger = defaultConfig.trigger;
		}

		// Create tooltip
		new Tooltip(el, config);
	}
}