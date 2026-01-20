async function refreshAvailability(){
  const date = document.querySelector('#date').value;
  const timeSelect = document.querySelector('#time');
  const availabilityHint = document.querySelector('#availabilityHint');

  if(!date){
    availabilityHint.textContent = "Kies eerst een datum.";
    return;
  }

  const res = await fetch(`/api/availability?date=${encodeURIComponent(date)}`);
  const data = await res.json();

  if(!data.ok){
    availabilityHint.textContent = "Kon beschikbaarheid niet laden.";
    return;
  }

  if(data.blocked){
    availabilityHint.textContent = "Deze datum is niet beschikbaar.";
  }else{
    availabilityHint.textContent = "Kies een tijdstip. Tijdsloten die bezet zijn verdwijnen automatisch.";
  }

  const allSlots = ["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"];
  const taken = new Set(data.taken || []);

  timeSelect.innerHTML = "";
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = data.blocked ? "Niet beschikbaar" : "Selecteer tijd";
  placeholder.disabled = true;
  placeholder.selected = true;
  timeSelect.appendChild(placeholder);

  if(data.blocked) return;

  for(const s of allSlots){
    if(!taken.has(s)){
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      timeSelect.appendChild(opt);
    }
  }
}

function setPackageDefaults(){
  const serviceType = document.querySelector('input[name="service_type"]:checked')?.value || "detailing";
  const packageSelect = document.querySelector('#package_code');
  packageSelect.innerHTML = "";

  const makeOpt = (value, label) => {
    const o = document.createElement("option");
    o.value = value;
    o.textContent = label;
    return o;
  };

  if(serviceType === "detailing"){
    packageSelect.appendChild(makeOpt("basic", "Basic pakket (€50)"));
    packageSelect.appendChild(makeOpt("deluxe", "Deluxe pakket (€100)"));
    packageSelect.appendChild(makeOpt("premium", "Premium pakket (€200)"));
  }else{
    packageSelect.appendChild(makeOpt("stage1", "Stage 1 — One Step Polish (€300)"));
    packageSelect.appendChild(makeOpt("stage2", "Stage 2 — Two Step Polish (vanaf €450)"));
    packageSelect.appendChild(makeOpt("stage3", "Stage 3 — Polish + Coating (vanaf €650)"));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const date = document.querySelector('#date');
  if(date){
    const today = new Date();
    const pad = (n)=> String(n).padStart(2,'0');
    const min = `${today.getFullYear()}-${pad(today.getMonth()+1)}-${pad(today.getDate())}`;
    date.min = min;
    date.addEventListener("change", refreshAvailability);
    refreshAvailability();
  }

  document.querySelectorAll('input[name="service_type"]').forEach(r => {
    r.addEventListener("change", () => {
      setPackageDefaults();
    });
  });

  setPackageDefaults();
});
