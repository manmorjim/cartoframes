import {
  resetPopupClick,
  resetPopupHover,
  setPopupsClick,
  setPopupsHover
} from './popups';

export function setInteractivity(map, interactiveLayers, interactiveMapLayers) {
  const interactivity = new carto.Interactivity(interactiveMapLayers);
  const popup = new mapboxgl.Popup({
    closeButton: false,
    closeOnClick: false
  });

  const { clickAttrs, hoverAttrs } = _setInteractivityAttrs(interactiveLayers);

  resetPopupClick(map, interactivity);
  resetPopupHover(map, interactivity);

  if (clickAttrs.length > 0) {
    setPopupsClick(map, popup, interactivity, clickAttrs);
  }

  if (hoverAttrs.length > 0) {
    setPopupsHover(map, popup, interactivity, hoverAttrs);
  }
}

function _setInteractivityAttrs(interactiveLayers) {
  let clickAttrs = [];
  let hoverAttrs = [];

  interactiveLayers.forEach((interactiveLayer) => {
    interactiveLayer.interactivity.forEach((interactivityDef) => {
      if (interactivityDef.event === 'click') {
        clickAttrs = clickAttrs.concat(interactivityDef.attrs);
      } else if (interactivityDef.event === 'hover') {
        hoverAttrs = hoverAttrs.concat(interactivityDef.attrs);
      }
    });
  });

  return { clickAttrs, hoverAttrs };
}