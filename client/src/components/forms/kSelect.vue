<template>
	<select v-if="group"
		v-model="value" 
		:class="classes" 
		:id="id" 
		:aria-label="label" 
		:disabled="disabled" 
		:required="required">
		<option value="" selected disabled>{{defaultText}}</option>
		<slot></slot>
	</select>
	<div v-else>
		<label v-if="label" :for="label" class="form-label">{{label}}</label>
		<select v-model="value" :class="classes" :id="id" :aria-label="label" :disabled="disabled" :required="required">
			<option value="" v-if="defaultText !== ''" selected disabled>{{defaultText}}</option>
			<slot></slot>
		</select>
		<k-input-validation invalid="Please select an option." />
	</div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref, toRefs, watch } from "vue";
import kInputValidation from "./kInputValidation.vue";

export default defineComponent({
	components: {kInputValidation},
	props: {
		label: {type: String, default: ""},
		defaultText: {type: String, default: "Please select"},
		disabled: {type: Boolean, default: false},
		required: {type: Boolean, default: false},
		group: {type: Boolean, default: false},
		size: {type: String, default: "default", validator(s: string) {return ["lg", "sm", "default",].indexOf(s) !== -1}},
		modelValue: {type: [String, Number] as PropType<string | number>, default: ""}
	},
	setup(props: Props, { emit }) {
		const { size, modelValue, label } = toRefs(props);

		const lg = size.value == "lg" ? "form-select-lg" : "";
		const sm = size.value == "sm" ? "form-select-sm" : "";
		const height = lg || sm;
		const classes = `form-select ${height}`;

		const value = ref(modelValue.value);
		watch(value, newVal => emit("update:modelValue", newVal));

		watch(modelValue, newVal => value.value = newVal);

		const id = label.value.replace(/\s+/g, '');

		return { classes, value, id };
	}
});

interface Props {
	label: string;
	defaultText: string;
	size: string;
	group: boolean;
	disabled: boolean;
	required: boolean;
	modelValue: string | number;
}
</script>