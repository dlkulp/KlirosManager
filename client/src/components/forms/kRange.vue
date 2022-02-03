<template>
	<div>
		<label class="form-label" :for="id">{{label}}</label>
		<input v-model="value" class="form-range" :id="id" type="range" :min="min" :max="max" :step="step" :disabled="disabled" />
	</div>
</template>

<script lang="ts">
import { defineComponent, toRefs, watch, ref } from "vue";

export default defineComponent({
	props: {
		min: {type: Number, default: 0},
		max: {type: Number, default: 100},
		step: {type: Number, default: 1},
		disabled: {type: Boolean, default: false},
		label: {type: String, default: ""},
		modelValue: {type: Number, default: 50}
	},
	setup(props, {emit}){
		const { modelValue } = toRefs(props);
		const value = ref(`${modelValue.value}`);
		const id = ref(`${Date.now()}${window.crypto.getRandomValues(new Uint32Array(1))[0]}`);

		watch(value, newVal => emit("update:modelValue", Number(newVal)));
		watch(modelValue, newVal => value.value = `${newVal}`);

		return { value, id };
	}
});
</script>

<style lang="scss" scoped>
</style>