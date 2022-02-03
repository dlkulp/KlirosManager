<template>
<main id="top" class="main" >
	<div class="container-fluid" data-layout="container">
		<slot />
	</div>
</main>
</template>

<script lang="ts" setup></script>
<style lang="scss">
.container-fluid{
	overflow: auto;
}
</style>