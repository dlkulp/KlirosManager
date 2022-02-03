<template>
	<div :class="classes">
		<input class="form-check-input" v-if="!value && !trueValue && !falseValue"
			:name="name" 
			:type="bType" 
			v-model="model" 
			:value="value" 
			:id="id" 
			:checked="checked" 
			:required="required" 
			:disabled="disabled">
		<input class="form-check-input" v-else
			:name="name" 
			:type="bType" 
			v-model="model"
			:value="value" 
			:id="id" 
			:checked="checked" 
			:required="required" 
			:disabled="disabled"
			:true-value="trueValue"
			:false-value="falseValue">
		<label class="form-check-label" v-if="label" :for="id">{{label}}</label>
		<k-input-validation v-if="invalidText" :invalid="invalidText" />
	</div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref, toRefs, watch } from "vue";
import kInputValidation from "./kInputValidation.vue";

export const baseProps = {
	label: {type: String, default: ""},
	checked: {type: Boolean, default: false},
	value: {type: [String, Object], default: ""},
	name: {type: String, default: ""},
	inline: {type: Boolean, default: false},
	disabled: {type: Boolean, default: false},
	required: {type: Boolean, default: false},
	trueValue: {type: [String, Boolean], default: true},
	falseValue: {type: [String, Boolean], default: false},
	invalidText: {type: String, default: ""}
};

export default defineComponent({
	components: {kInputValidation},
	props: {
		...baseProps, 
		type: {type: String, default: "checkbox", validator(t: string) { return ["checkbox", "radio", "switch"].indexOf(t) !== -1; }},
		checkValue: {type: [String, Array, Boolean] as PropType<string | string[] | Boolean>, default: ""}
	},	
	setup(props: BaseProps, { emit }) {
		const { type, inline, checkValue, trueValue, falseValue, label } = toRefs(props);

		// Input classes
		const bSwitch = type.value === "switch" ? "form-switch" : "";
		const bInline = inline.value ? "form-check-inline" : "";
		const classes = ref(`form-check ${bSwitch} ${bInline}`);

		// Type
		const bType = ref("");
		bType.value = type.value === "switch" ? "checkbox" : type.value;

		// Model binding
		const model = ref(checkValue.value);

		// Bubble changes up to original context
		watch(model, newVal => {
			emit("update:checkValue", newVal);
		});

		watch(checkValue, newVal => model.value = newVal);

		// If trueValue and falseValue are used, make sure they're assigned to the model ref
		if (trueValue.value && falseValue.value)
			model.value = model.value == trueValue.value ? trueValue.value : falseValue.value;

		const id = label.value.replace(/\s+/g, '');

		return { classes, bType, model, id };
	}
});

export interface Props {
	label: string;
	checked: boolean;
	value: string | object;
	name: string;
	inline: boolean;
	required: boolean;
	disabled: boolean;
	trueValue: string | boolean;
	falseValue: string | boolean;
	invalidText: string;
}

interface BaseProps extends Props {
	checkValue: string | string[] | Boolean;
	type: string;
}
</script>