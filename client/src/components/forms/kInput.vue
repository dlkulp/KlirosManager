<template>
	<input-mask v-if="group"
		:type="type" 
		v-model:inpValue="value"
		:label="label" 
		:size="size" 
		:required="required" 
		:disabled="disabled" 
		:readonly="readonly"
		:feedback="false"
		:placeholder="placeholder">
	</input-mask>
	<k-input-group v-else-if="type === 'currency'" :label="label" :disableFeedback="true">
		<k-input-group-text>$</k-input-group-text>
		<input-mask
			:type="type" 
			v-model:inpValue="value"
			:label="label"  
			:size="size" 
			:required="required" 
			:disabled="disabled || readonly"
			:feedback="feedback"
			:placeholder="placeholder">
		</input-mask>
	</k-input-group>
	<div v-else-if="type === 'datetime' || type === 'date' || type === 'time'">
		<label v-if="label" :for="label" class="form-label">{{label}}</label>
		<flat-pickr
			v-model="value" 
			:config="type === 'datetime' ? dtConfig : (type == 'date' ? dateConfig : timeConfig)" 
			:placeholder="datePlaceholder" 
			:name="label" 
			:class="`form-control ${size !== 'default' ? `form-control-${size}` : ''}`"
			:required="required" 
			:disabled="disabled">
		</flat-pickr>
		<k-input-validation v-if="feedback" invalid="Please select a date" />
	</div>
	<div v-else>
		<label v-if="label" :for="label" class="form-label">{{label}}</label>
		<input-mask
			:type="type" 
			v-model:inpValue="value"
			:label="label" 
			:size="size" 
			:required="required" 
			:disabled="disabled" 
			:readonly="readonly"
			:feedback="feedback"
			:placeholder="placeholder">
		</input-mask>
	</div>
</template>

<script lang="ts">
import { defineComponent, ref, toRefs, watch } from "vue";
import inputMask from "./_inputMask.vue";
import kInputGroup from "./kInputGroup.vue";
import kInputGroupText from "./kInputGroupText.vue";
import kInputValidation from "./kInputValidation.vue";
import flatPickr from "vue-flatpickr-component";

export default defineComponent({
	components: {inputMask, kInputGroup, kInputGroupText, kInputValidation, flatPickr},
	props: {
		label: {type: String, default: ""},
		disabled: {type: Boolean, default: false},
		readonly: {type: Boolean, deafult: false},
		required: {type: Boolean, default: false},
		group: {type: Boolean, default: false},
		feedback: {type: Boolean, default: true},
		size: {type: String, default: "default", validator(s: string) {return ["lg", "sm", "default",].indexOf(s) !== -1}},
		type: {type: String, default: "text", validator(t: string) {return ["text", "number", "phone", "ssn", "currency", "zip", "ein", "email", "date", "datetime", "time"].indexOf(t) !== -1}},
		dateTimeConfig: {type: Object, default: {}},
		modelValue: {type: String || Number, default: ""},
		placeholder: {type: String || Number, default: ""},
	},
	setup(props: Props, { emit }) {
		const { modelValue, dateTimeConfig, type } = toRefs(props);
		const value = ref(modelValue.value);
		
		// Flatpickr placeholder text
		const datePlaceholder = ref("");
		
		// Flatpickr configuration
		const dateConfig = {
			altInput: true,
			allowInput: true,
			altFormat: "m/d/Y",
			dateFormat: "Y-m-d"
		};

		const timeConfig = {
			altInput: true,
			allowInput: true,
			enableTime: true,
			altFormat: "h:i K",
			dateFormat: "H:i",
			noCalendar: true
		};

		const dtConfig = {
			altInput: true,
			allowInput: true,
			enableTime: true,
			altFormat: "m/d/Y h:i K",
			dateFormat: "Y-m-d\\TG:i:S"
		};

		// Setup each of the three configs with overrides
		let configs: any[] = [dateConfig, timeConfig, dtConfig];
		for (let config of configs)
			for (let key of Object.keys(dateTimeConfig.value))
				config[key] = (dateTimeConfig.value as any)[key];

		if (type.value === "date")
			datePlaceholder.value = "__/__/____";
		else if (type.value === "time")
			datePlaceholder.value = "__:__ __";
		else if (type.value === "datetime")
			datePlaceholder.value = "__/__/____ __:__ __";

		// Bubble changes up to original context
		watch(value, newVal => emit("update:modelValue", newVal));
		watch(modelValue, newVal => value.value = newVal);

		return { value, dateConfig, timeConfig, dtConfig, datePlaceholder };
	}
});

interface Props {
	label: string;
	disabled: boolean;
	readonly: boolean;
	required: boolean;
	group: boolean;
	feedback: boolean;
	size: string;
	type: string;
	modelValue: string;
	dateTimeConfig: Object;
	placeholder: string;
}
</script>