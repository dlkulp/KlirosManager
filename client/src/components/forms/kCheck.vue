<template>
	<check-radio v-if="!value && !trueValue && !falseValue"
		:label="label" 
		type="checkbox" 
		:checked="checked"
		:name="name" 
		:inline="inline"
		v-model:checkValue="model"
		:required="required" 
		:disabled="disabled"
		:invalidText="invalidText">
	</check-radio>
	<check-radio v-else
		:label="label" 
		type="checkbox" 
		:checked="checked"
		:value="value" 
		:name="name" 
		:inline="inline"
		v-model:checkValue="model"
		:required="required" 
		:disabled="disabled"
		:true-value="trueValue"
		:false-value="falseValue"
		:invalidText="invalidText">>
	</check-radio>
</template>

<script lang="ts">
import { defineComponent, PropType, ref, toRefs, watch } from "vue";
import checkRadio, { baseProps } from "./_checkRadio.vue";

export default defineComponent({
	props: {
		...baseProps,
		modelValue: {type: [String, Array, Object, Boolean] as PropType<string | string[]>, default: ""}
	},
	components: {checkRadio},
	setup(props, { emit }) {
		const { modelValue } = toRefs(props);

		// Model binding
		const model = ref(modelValue.value);

		// Bubble changes up to original context
		watch(model, newVal => emit("update:modelValue", newVal));

		watch(modelValue, newVal => model.value = newVal);

		return {model};
	}
});
</script>