<script setup lang="ts">
import ourFather from "../assets/Our Father.png";
import kCard from "../components/cards/kCard.vue";

let score = {
	id: "1",
	title: "Our Father",
	img: {url: ourFather, alt: "Our Father Music"},
	metaData: {
		"Tone Set": "Strochnoi",
		"Tone": 2,
		"Chorus": "Mixed",
		"Parts": 3,
		"Service": ["Liturgy"],
		"Language": "English",
		"Part of Service": "Our Father",
		"Feast": ""
	}
};
</script>
<template>
<div class="">
	<h1>Title</h1>
	<div id="viewer"></div>
	<kCard id="meta">
		<template #header>Metadata</template>
		default
	</kCard>
	<div id="actions"></div>
</div>
</template>
<style scoped lang="scss">

</style>