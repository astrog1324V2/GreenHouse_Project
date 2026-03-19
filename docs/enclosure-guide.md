# Greenhouse Enclosure Build Guide

This enclosure should protect the electronics without trapping the air that your sensors need to measure.

## 1. Use a two-compartment design

- `electronics bay`: ESP32, OLED wiring, USB power entry, cable joins, silica packs
- `sensor bay`: DHT22 and BH1750 only

Do not combine these into one airtight box. The electronics want protection from moisture. The DHT22 needs open airflow.

## 2. Electronics bay

- Make this the sealed compartment.
- Add a raised lip and use thin foam gasket tape around the lid.
- Use screws so you can reopen it later.
- Bring the USB cable through a printed strain-relief channel or a cable gland.
- Add one or two small silica gel packs here only.
- Leave enough space for airflow around the ESP32 so it does not get hotter than necessary.

## 3. Sensor bay

- Keep this compartment vented on multiple sides.
- Use slots or louvers instead of one large hole.
- Add insect mesh behind the vents.
- Keep the DHT22 away from the ESP32 board and display heat.
- Make the DHT22 replaceable with screws, clips, or a removable sensor insert.

The DHT22 should sample outside air, not trapped enclosure air.

## 4. BH1750 placement

- Give the BH1750 a direct light path.
- Best option: a small dedicated top opening or window just for the light sensor.
- Keep that opening shielded so rain cannot fall straight in.
- Avoid putting the entire enclosure under a large clear roof. Clear covers can trap heat and distort readings.

## 5. Outdoor unit shape

- Use a white or light-colored roof and outer shell.
- Add a roof overhang and drip edge.
- Mount the sensor bay below the roof so it stays shaded and ventilated.
- A small radiation-shield style stack or louvered chimney shape works well for the DHT22.
- Do not mount it directly against a sun-heated wall, metal post, or greenhouse panel.

If you build a small shelter next to the greenhouse, make the roof opaque or mostly opaque instead of fully clear.

## 6. Greenhouse unit shape

- Keep the OLED on the front face behind a bezel or window opening.
- Separate the display space from the sensor airflow path.
- Put the sensor vents where they see greenhouse air directly, not warm air trapped behind the screen.
- Mount the unit where it will not be splashed during watering.

## 7. Serviceability

- Use screws for the lid instead of glue.
- Make the sensor section removable if possible.
- Leave access to the USB connector or power wires.
- Add mounting holes or zip-tie slots in the model now.
- Label internal standoffs or sensor mounting points in the CAD model so reassembly is obvious.

## 8. Printing recommendations

- Prefer PETG for outdoor use. It handles heat and humidity better than PLA.
- Use light colors outside, especially white, cream, or light gray.
- Print enough wall thickness that the screw holes and lid lip do not crack.
- Use rounded edges and fillets where possible to reduce stress around mounting tabs.

## 9. Practical sizing checklist

- Measure the ESP32 board with headers installed.
- Measure the OLED depth including the connector.
- Leave room for the USB cable bend radius.
- Leave clearance for sensor replacement by hand.
- Test-fit the breadboard layout before committing to the final print, or redesign to avoid keeping a full breadboard inside the final enclosure.

## 10. What not to do

- Do not put silica packs in the same air chamber as the DHT22.
- Do not make the sensor chamber airtight.
- Do not hide the BH1750 behind thick tinted plastic.
- Do not let the DHT22 sit in direct sun.
- Do not permanently glue the enclosure closed.
