<template>
	<check-radio 
		:label="label" 
		type="radio" 
		:checked="checked"
		:value="value" 
		:name="name" 
		:inline="inline"
		v-model:checkValue="model"
		:required="required" 
		:disabled="disabled"
		:invalidText="invalidText">
	</check-radio>
</template>

<script lang="ts">
import { defineComponent, ref, toRefs, watch } from "vue";
import checkRadio, {baseProps, Props} from "./_checkRadio.vue";

export default defineComponent({
	props: {
		...baseProps,
		modelValue: {type: String, default: ""}
	},
	components: {checkRadio},
	setup(props: RadioProps, { emit }) {
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

interface RadioProps extends Props {
	modelValue: string;
}
</script>