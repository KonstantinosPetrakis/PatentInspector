<script setup></script>

<style>
.tab-item {
    display: none;
}
.tab-item.active {
    display: block;
}
</style>

<template>
    <div class="tab-item">
        <slot></slot>
    </div>
</template>
