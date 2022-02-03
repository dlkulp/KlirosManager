<template>
	<check-radio 
		:label="label" 
		type="switch" 
		:checked="checked"
		:value="value" 
		:name="name" 
		:inline="inline"
		v-model:checkValue="model"
		:required="required" 
		:disabled="disabled"
		:true-value="trueValue"
		:false-value="falseValue"
		:invalidText="invalidText">
	</check-radio>
</template>

<script lang="ts">
import { defineComponent, PropType, ref, toRefs, watch } from "vue";
import checkRadio, {baseProps, Props} from "./_checkRadio.vue";

export default defineComponent({
	props: {
		...baseProps,
		modelValue: {type: [String, Array, Boolean] as PropType<string | string[] | Boolean>, default: ""}
	},
	components: {checkRadio},
	setup(props: ToggleProps, { emit }) {
		const { modelValue } = toRefs(props);

		// Model binding
		const model = ref(modelValue.value);

		// Bubble changes up to original context
		watch(model, newVal => {
			emit("update:modelValue", newVal);
		});

		watch(modelValue, newVal => model.value = newVal);

		return {model};
	}
});

interface ToggleProps extends Props {
	modelValue: string | string[] | Boolean;
}
</script>