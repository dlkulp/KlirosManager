<template>
  <div :class="`all-works fit row wrap justify-${justify} items-start content-start`">
        <q-btn flat
          v-for="(score, index) in scoreArr"
          :key="`${score.title}-${index}`"
          :to="score.detail_url">
          <q-card>
            <q-card-section>
              <img
                :src="score.thumbnail_url || ''"
                :srcset="score.thumbnail_srcset || ''"
                sizes="(max-width: 600px) 45vw, (max-width: 900px) 30vw, 300px"
                alt="Score thumbnail"
                loading="lazy"
                width="232"
                height="300" />
            </q-card-section>
            <q-card-section class="title-section column justify-center">
              <div class="text-center">{{ score.title || score.OriginalName || "Untitled" }}</div>
            </q-card-section>
          </q-card>
        </q-btn>
      </div>
</template>

<style lang="scss">
.title-section {
  padding-top: 0px;
}
.title-section div {
  font-size: 1.25rem;
  font-weight: bold;
  width: 207px;
  height: 1em;
  margin: auto;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.all-works a {
  width: 300px;
}
.all-works .q-btn {
  text-transform: none;
}
</style>

<script setup lang="ts">
import { ResourceDto } from '@/types/api-client';

export interface ScoreGridProps {
  scoreArr: ResourceDto[];
  justify?: string;
}

withDefaults(defineProps<ScoreGridProps>(), {
  justify: "start"
});
</script>
