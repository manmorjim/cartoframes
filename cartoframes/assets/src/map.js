import { BASEMAPS, attributionControl, FIT_BOUNDS_SETTINGS } from './constants';
import { createDefaultLegend } from './legends';
import { displayError } from './errors/display';
import { setInteractivity } from './map/interactivity';
import { updateViewport, getBasecolorSettings, saveImage } from './utils';
import { initMapLayer, getInteractiveLayers } from './layers';

export function setReady(settings) {
  try {
    return settings.maps ? initMaps(settings.maps) : initMap(settings);
  } catch (e) {
    displayError(e);
  }
}

export function initMaps(maps) {
  return maps.map((mapSettings, mapIndex) => {
    return initMap(mapSettings, mapIndex);
  });
}

export function initMap(settings, mapIndex) {
  const basecolor = getBasecolorSettings(settings.basecolor);
  const basemapStyle =  BASEMAPS[settings.basemap] || settings.basemap || basecolor;
  const container = mapIndex !== undefined ? `map-${mapIndex}` : 'map';
  const map = createMap(container, basemapStyle, settings.bounds, settings.mapboxtoken);

  if (settings.show_info) {
    updateViewport(map);
  }

  if (settings.camera) {
    map.flyTo(settings.camera);
  }

  return initLayers(map, settings, mapIndex);
}

export function initLayers(map, settings, mapIndex) {
  const numLayers = settings.layers.length;
  const hasLegends = settings.has_legends;
  const isDefaultLegend = settings.default_legend;
  const isStatic = settings.is_static;
  const layers = settings.layers;
  const mapLayers = getMapLayers(
    layers,
    numLayers,
    hasLegends,
    map,
    mapIndex
  );

  createLegend(isDefaultLegend, mapLayers);
  setInteractiveLayers(map, layers, mapLayers);

  return waitForMapLayersLoad(isStatic, mapIndex, mapLayers);
}

export function waitForMapLayersLoad(isStatic, mapIndex, mapLayers) {
  return new Promise((resolve) => {
    carto.on('loaded', mapLayers, onMapLayersLoaded.bind(
      this, isStatic, mapIndex, mapLayers, resolve)
    );
  });
}

export function onMapLayersLoaded(isStatic, mapIndex, mapLayers, resolve) {
  if (isStatic) {
    saveImage(mapIndex);
  }

  resolve(mapLayers);
}

export function getMapLayers(layers, numLayers, hasLegends, map, mapIndex) {
  return layers.map((layer, layerIndex) => {
    return initMapLayer(layer, layerIndex, numLayers, hasLegends, map, mapIndex);
  });
}

export function setInteractiveLayers(map, layers, mapLayers) {
  const { interactiveLayers, interactiveMapLayers } = getInteractiveLayers(layers, mapLayers);

  if (interactiveLayers && interactiveLayers.length > 0) {
    setInteractivity(map, interactiveLayers, interactiveMapLayers);
  }
}

export function createLegend(isDefaultLegend, mapLayers) {
  if (isDefaultLegend) {
    createDefaultLegend(mapLayers);
  }
}

export function createMap(container, basemapStyle, bounds, accessToken) {
  const map = createMapboxGLMap(container, basemapStyle, accessToken);

  map.addControl(attributionControl);
  map.fitBounds(bounds, FIT_BOUNDS_SETTINGS);

  return map;
}

export function createMapboxGLMap(container, style, accessToken) {
  if (accessToken) {
    mapboxgl.accessToken = accessToken;
  }

  return new mapboxgl.Map({
    container,
    style,
    zoom: 9,
    dragRotate: false,
    attributionControl: false
  });
}