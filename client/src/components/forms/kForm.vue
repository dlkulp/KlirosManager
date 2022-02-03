<template>
    <form ref="formRef" class="needs-validation" novalidate>
        <slot />
    </form>
</template>

<script lang="ts" setup>
import { ref, Ref, onMounted } from "vue";

const formRef: Ref<HTMLInputElement | null> = ref(null);

onMounted(() => {
	if (!formRef.value) return;
	formRef.value.addEventListener("submit", function(event) {
		if (!formRef.value?.checkValidity()) {
			event.preventDefault();
			event.stopPropagation();
		}

		formRef.value?.classList.add("was-validated");
		return false;
	}, false)
});
</script>