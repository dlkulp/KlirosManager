<script setup lang="ts">
import Knob from "primevue/knob";
import Chip from "primevue/chip";
import { ref } from "vue";

let knobby = ref(0);
</script>

<template>
	<section class="about">
		<h1>About</h1>
		<p>Put in some UI stuff</p>
		<Knob v-model="knobby"></Knob>
		<Chip label="Chip with icon" icon="pi pi-check" class="p-mr-2 p-mb-2 custom-chip" />
	</section>
</template>

<style lang="scss" scoped>
.p-chip.custom-chip {
    background: var(--primary-color);
    color: var(--primary-color-text);
}
</style>