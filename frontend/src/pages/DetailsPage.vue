<template>
  <q-page v-if="detail">
    <q-layout view="hhh lpr fff" max-width="720px">
      <q-header>
        <h4>{{ title }}</h4>
        <p>{{ subtitle }}</p>
      </q-header>
      <q-page-container id="score">
        <PdfViewer
            v-if="detail"
            :source="detail.file_url"
            style="height: 100%;width: 98%"
            :show-thumbnails="false"
            :enable-search="false"
            :enable-download="false"
            :lazy="true"
            :virtualization="true"
            :text-layer="false"
            theme="auto"
          />
      </q-page-container>
      <q-drawer show side="right" persistent id="metadata" v-model="showDrawer" elevated :overlay="false">
        <q-card>
          <p>Metadata at a glance</p>
        </q-card>
        <template v-for="(value, key) in detail.metadata" :key="key">
          <q-card>
            <p>{{ key }}</p>
            <p>{{ value }}</p>
          </q-card>
        </template>
      </q-drawer>
    </q-layout>
  </q-page>
</template>

<style scoped lang="scss">
h4 {
  margin-bottom: 0px;
}
#score {
  width:100%;
}
.q-header {
  background-color: $grey-9 !important;
}
</style>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ResourceDetailResponseDto, KlirosApi } from "@/types/api-client";

import { PdfViewer } from "vue-pdfz";
import "vue-pdfz/style.css";

const { scoreId } = defineProps<{
  scoreId: string;
}>();

const detail = ref<ResourceDetailResponseDto | null>(null);
const api = new KlirosApi();
const title = ref<string>();
const subtitle = ref<string>();
const showDrawer = ref(true);

onMounted(async() => {
  try {
    detail.value = await api.getResource(Number(scoreId));
    let english: boolean = detail.value.metadata?.["English Title"] !== undefined;
    title.value = detail.value.metadata?.["English Title"] || detail.value.resource.title || detail.value.resource.OriginalName || "Untitled";
    subtitle.value = english ? `${detail.value.resource.title} - ${detail.value.resource.OriginalName}` : detail.value.resource.OriginalName;
  } catch (error) {
    // detailStatus.textContent = error instanceof Error ? error.message : "The score could not be loaded.";
    // detailStatus.hidden = false;
    console.error(error);
  }

});
</script>
