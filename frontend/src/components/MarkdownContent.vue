<script setup lang="ts">
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

const props = defineProps<{ content: string }>()
const markdown = new MarkdownIt({ html: false, linkify: true, breaks: true })
const rendered = computed(() => DOMPurify.sanitize(markdown.render(props.content || '')))
</script>

<template>
  <div class="markdown-content" v-html="rendered"></div>
</template>
