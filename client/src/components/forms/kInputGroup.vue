<template>
	<div>
		<label v-if="label" :for="label" class="form-label">{{label}}</label>
		<div :class="`${classes} has-validation`">
			<slot></slot>
			<k-input-validation v-if="!disableFeedback" :invalid="invalidText"></k-input-validation>
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent, toRefs } from "vue";
import kInputValidation from "./kInputValidation.vue";

export default defineComponent({
	components: {kInputValidation},
	props: {
		label: {type: String, default: ""},
		size: {type: String, default: "default", validator(s: string) {return ["lg", "sm", "default",].indexOf(s) !== -1}},
		invalidText: {type: String, default: "Please fill this out."},
		disableFeedback: {type: Boolean, default: false}
	},
	setup(props: Props) {
		const {size} = toRefs(props);
		const lg = size.value == "lg" ? "input-group-lg" : "";
		const sm = size.value == "sm" ? "input-group-sm" : "";
		const height = lg || sm;
		const classes = `input-group ${height}`;

		return { classes };
	}
});

interface Props {
	label: string;
	size: string;
	invalidText: string;
}
</script>