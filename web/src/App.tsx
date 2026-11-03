import { MapContainer, TileLayer } from "react-leaflet"
import type { LatLngExpression } from "leaflet"

const MELBOURNE: LatLngExpression = [-37.8136, 144.9631]

function App() {
  return (
    <MapContainer center={MELBOURNE} zoom={11} className="map">
      <TileLayer
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
    </MapContainer>
  );
}

export default App;