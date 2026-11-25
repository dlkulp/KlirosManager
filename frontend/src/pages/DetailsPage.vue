<template>
  <q-page v-if="detail">
    <div class="center-stripe">
      <section class="lighten q-pa-md">
        <h4>{{ title }}</h4>
        <p v-if="!english">{{ detail.resource.DisplayName }}</p>
      </section>
      <section class="row no-wrap justify-between q-mb-xs">
        <q-btn to="/library" icon="arrow_back">Back to Library</q-btn>
        <div right>
          <q-btn
            v-if="store.isLoggedIn"
            :color="starred ? 'orange' : ''"
            :text-color="starred ? '' : 'orange'"
            :icon="starred ? 'star' : 'star_outline'"
            class="q-mr-sm"
            @click="starToggle(detail.resource.id)">
            &nbsp;&nbsp;<span v-if="starred">Un</span>Favorite
          </q-btn>
          <q-btn
            color="secondary"
            :href="detail.download_url"
            :download="`${detail.resource.DisplayName} - ${attribution}.pdf`"
            icon="download">
            Download
          </q-btn>
        </div>
      </section>
      <section class="row">
        <div id="score" class="col-xs-12 col-md-9 col-xl-10">
          <PdfViewer
              v-if="detail"
              :source="detail.file_url"
              style="width: 98%; margin:auto;"
              layout="single"
              :show-thumbnails="false"
              :enable-search="false"
              :enable-download="false"
              :lazy="true"
              :virtualization="true"
              :text-layer="false"
              theme="auto"
            />
        </div>
        <div id="info" class="col-xs-12 col-md-3 col-xl-2 q-pa-md text-body2">
          <h6>Uploaded by:</h6>
          <q-btn outline :to="`/profile/${detail.uploader.UserID}`" class="q-mt-sm q-mb-sm q-pl-sm q-pr-sm">
            <div class="row items-center no-wrap">
              <q-avatar left text-color="white" color="primary" rounded size="2rem">
                {{ detail.uploader_initials }}
              </q-avatar>
              <span class="text-center q-pa-sm text-capitalize text-caption">
                {{ detail.uploader.Name }}<br />
                <span class="text-caption text-weight-thin">Joined: {{ detail.uploader.JoinedAt }}</span>
              </span>
            </div>
          </q-btn>
          <div>
            Downloaded: {{ detail.resource.DownloadCount }} times
          </div>
          <div class="q-mt-md">
            <h6>At a glance:</h6>
            <q-card>
              <q-card-section>
                <template  v-for="(value, key) in detail.metadata" :key="key">
                  <p class="q-mb-xs">{{ key }}</p>
                  <p class="text-caption text-weight-thin">{{ value }}</p>
                </template>
              </q-card-section>
            </q-card>
          </div>
          <div class="q-mt-md" id="actions">
            <h6>Actions:</h6>
            <div class="">
              <template v-if="owner">
                <q-btn icon="edit" color="info" class="text-body2 q-ma-xs">&nbsp;Edit</q-btn>
                <q-btn icon="delete" color="negative" class="text-body2 q-ma-xs" @click="promptDelete()">&nbsp;Delete</q-btn>
              </template>
              <q-btn icon="flag" color="warning" class="text-body2 q-ma-xs">&nbsp;Report</q-btn>
            </div>
          </div>
        </div>
      </section>
    </div>
  </q-page>
</template>

<style scoped lang="scss">
#info {
  height: auto !important;
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ResourceDetailResponseDto, KlirosApi } from "@/types/api-client";
import { store } from "@/helpers/store";
import { PdfViewer } from "vue-pdfz";
import "vue-pdfz/style.css";
import { useRouter } from "vue-router";
import { useQuasar } from "quasar";

const { scoreId } = defineProps<{
  scoreId: string;
}>();
const $q = useQuasar();
const starred = ref<boolean>(false);
const router = useRouter();

async function promptDelete() {
  $q.dialog({
    title: "Confirm delete?",
    message: "Are you sure you want to remove this score from the library? Files and saved relationships will remain.",
    cancel: true,
    persistent: true
  }).onOk(deleteRec);
}

async function deleteRec() {
  if (detail.value) {
    let resp = await api.deleteResource(detail.value.resource.id);
    if (resp.deleted)
      await router.replace("/library");
  }
}

async function starToggle(resourceId: number) {
  try {
    let resp = await api.toggleFavorite(resourceId);
    starred.value = resp.is_favorite;
  }
  catch (error) {
    console.log(error);
  }
}

const detail = ref<ResourceDetailResponseDto | null>(null);
const api = new KlirosApi();
const title = ref<string>();
const english = ref<boolean>(true);
const attribution = ref<string>();
const owner = computed(() => {
  if (detail.value)
    return detail.value.uploader.UserID === store.user?.user.UserID;
  return false;
});

onMounted(async() => {
  try {
    detail.value = await api.getResource(Number(scoreId));
    english.value = detail.value.metadata?.["English Title"] === undefined;
    title.value = detail.value.metadata?.["English Title"] || detail.value.resource.title || "Untitled";
    attribution.value = detail.value.metadata?.["Composer"] || detail.value.metadata?.["Arranger"] || "Unknown";
    // Show date in prettier form
    let joinDate = new Date(detail.value.uploader.JoinedAt);
    detail.value.uploader.JoinedAt = `${joinDate.getMonth()+1}/${joinDate.getFullYear()}`;
    // check starred state
    if (store.user) {
      starred.value = store.user.favorites.filter(i => i.id === detail.value?.resource.id ).length > 0;
    }
  } catch (error) {
    // detailStatus.textContent = error instanceof Error ? error.message : "The score could not be loaded.";
    // detailStatus.hidden = false;
    console.error(error);
  }
});
</script>
