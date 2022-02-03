<template>
    <input ref="inp" 
		:type="inputType" 
		@input="onChanged" 
		:id="id" 
		:value="inpValue" 
		:pattern="validator" 
		:class="classes" 
		:required="required" 
		:disabled="disabled || readonly" 
		:readonly="readonly"
		:placeholder="placeholder">
	<k-input-validation v-if="feedback" :invalid="invalid" />
</template>

<script lang="ts">
import { defineComponent, toRefs, ref, Ref, onMounted } from "vue";
import Inputmask from "inputmask";
import kInputValidation from "./kInputValidation.vue";

export default defineComponent({
	components: {kInputValidation},
	props: {
		label: {type: String, default: ""},
		disabled: {type: Boolean, default: false},
		readonly: {type: Boolean, deafult: false},
		required: {type: Boolean, default: false},
		feedback: {type: Boolean, default: true},
		size: {type: String, default: "default", validator(s: string) {return ["lg", "sm", "default",].indexOf(s) !== -1}},
        type: {type: String, default: "text", validator(t: string) {return ["text", "number", "phone", "ssn", "currency", "zip", "ein", "email"].indexOf(t) !== -1}},
		inpValue: {type: String || Number, default: ""},
		placeholder: {type: String || Number, default: ""},
	},
	// -- 'text',
	// -- 'number',
	// -- 'email',
	// 'password',
	// 'search',
	// 'url',
	// -- 'tel',
	// 'date',
	// 'time',
	// 'range',
	// 'color'
	setup(props: Props, { emit }) {
        const {type, size, readonly, label} = toRefs(props);

        // Form control classes
		const lg = size.value == "lg" ? "form-control-lg" : "";
		const sm = size.value == "sm" ? "form-control-sm" : "";
		const height = lg || sm;
		const formControl = `form-control${readonly.value ? "-plaintext" : ""}`;
        const classes = ref(`${formControl} ${height}`);
        
        // Bubble changes up to original context
		let onChanged = (e: Event) => {
			// Remove special characters: ()[space]-,
			// let removeReg = new RegExp("");
			// // Leave everything for general text
			// if (type.value !== "text" && type.value !== "email")
			// 	removeReg = /[()\s\-,@]/g;
			if (e?.currentTarget) {
				let val = (<HTMLInputElement>e.currentTarget).value;//.replace(removeReg, "");

				emit("update:inpValue", val);
			}
		}
		
		// Validation
		const invalid = ref("");
        
        // Input mask stuff
		const inputType = ref("text");
		let mask = "";
		let options = {};
		const validator = ref();
        const inp: Ref<HTMLInputElement | null> = ref(null);

        switch(type.value) {
			case "number":
				mask = "numeric";
				validator.value = "-?(\\d{1,3})+(,\\d{3})*(?:\\.\\d+)?";
				invalid.value = "Please provide a number.";
				options = {greedy: false, rightAlign: false};
				break;
			case "email":
				mask = `email`;
				validator.value = `^[a-zA-Z0-9.!#$%&'*+/=?^_\`{|}~-]+@[a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)*$`;
				invalid.value = "Please provide a complete email address";
				break;
			case "phone":
				mask = "(999) 999-9999";
				validator.value = "\\(\\d{3}\\) \\d{3}-\\d{4}";
				invalid.value = "Please provide a phone number.";
				break;
			case "ssn":
				mask = "ssn";
				validator.value = "\\d{3}-\\d{2}-\\d{4}";
				invalid.value = "Please provide an ssn.";
				break;
			case "ein":
				mask = "99-9999999";
				validator.value = "\\d{2}-\\d{7}";
				invalid.value = "Please provide an ein.";
				break;
			case "currency":
				mask = "currency";
				validator.value = "-?\\d{1,3}(,\\d{3})*(?:\\.\\d{2})?";
				invalid.value = "Please provide a value.";
				options = {greedy: false, rightAlign: false};
				break;
			case "zip":
				mask = "99999[-9999]";
				validator.value = "\\d{5}(?:-\\d{4})?";
				invalid.value = "Please provide a 5 or 9 digit zip code.";
				options = {greedy: false, rightAlign: false};
				break;
			case "text":
			default:
				mask = "";
				validator.value = ".*";
				invalid.value = "Please fill this out.";
        }

		onMounted(() => {
			Inputmask(mask, options).mask(<HTMLInputElement>inp.value);
		});
		
		const id = label.value.replace(/\s+/g, '') || window.crypto.getRandomValues(new Uint32Array(1))[0].toString(16);
        
        return { inputType, onChanged, inp, invalid, classes, validator, id };
    }
});

interface Props {
	label: string;
	disabled: boolean;
	readonly: boolean;
	required: boolean;
	size: string;
	type: string;
	inpValue: string;
	placeholder: string;
}
</script>