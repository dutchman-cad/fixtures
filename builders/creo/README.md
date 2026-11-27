# Creo Parametric Fixture Builder

Downloads: [probe_creo.ps1](https://fixtures.dutchmancad.xyz/builders/creo/probe_creo.ps1) (VB API probe),
[probe_creo.html](https://fixtures.dutchmancad.xyz/builders/creo/probe_creo.html) (Creo.JS probe), and the builder kit:
[KIT.md](https://fixtures.dutchmancad.xyz/builders/creo/KIT.md),
[creo_fixtures.json](https://fixtures.dutchmancad.xyz/builders/creo/creo_fixtures.json),
[build_creo.html](https://fixtures.dutchmancad.xyz/builders/creo/build_creo.html),
[pack_creo.ps1](https://fixtures.dutchmancad.xyz/builders/creo/pack_creo.ps1),
[creo_recipes.creojs](https://fixtures.dutchmancad.xyz/builders/creo/creo_recipes.creojs) (the file your code goes in).

Creo's free scripting (Creo.JS, the VB API and free J-Link, which share one API) can open, copy, change, assemble,
measure, save and export models, but can't create a sketched feature: PTC's reference lists `CreateFeature` as not
implemented. So the Creo builder is a Creo.JS page that runs every design, checks it against the answer key and
packs it, around one function per design that a contributor writes (template parts, UDFs, mapkeys), plus files
made by hand that it opens and checks. Twins whose only change is one number it makes itself. **Start with
[KIT.md](https://fixtures.dutchmancad.xyz/builders/creo/KIT.md).**

The probes below tell us what a given Creo install can script. Each takes about 3 minutes.

## Run the probe

1. Save your work and close Creo. The probe starts a Creo session of its own in the background, and some licenses
   allow only one session at a time.
2. Download `probe_creo.ps1` into your Downloads folder.
3. Click **Start**, type `PowerShell`, and click **Windows PowerShell** (not PowerShell 7, not ISE).
4. Paste this line and press **Enter**:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\probe_creo.ps1"
   ```

5. Wait until it prints `Creo probe: N of M checks passed`. It may take a minute before Creo answers; no Creo
   window opens unless the background start fails, in which case it tries once more with a window.
6. The last line is the path of a zip, in a new `probe_creo-…` folder under `C:\Users\Public\FixtureOut\CreoProbe`
   (outside your user folder: Creo writes the folder it saves in into every file). Send that zip
   to **Dutchy** in a Discord direct message.

If several Creo releases are installed, the probe uses the newest. To probe another one, add its program, for
example `-CreoExe "C:\Program Files\PTC\Creo 9.0.4.0\Parametric\bin\parametric.exe"` at the end of the line in
step 4. To read the install without starting Creo at all, add `-NoStart`.

## Run the Creo.JS probe too (if you use Creo.JS)

The same checks, through Creo.JS instead of the VB API. It needs the `creojs.js` file from your own Creo.JS setup
(we don't ship PTC's files).

1. Make a new empty folder outside your user folder: `C:\Users\Public\FixtureOut\creo-probe`. The probe saves
   nothing in a folder inside your user folder, OneDrive or a network share.
2. Download `probe_creo.html` into it, and copy `creojs.js` from your Creo.JS setup next to it (the same file your
   own Creo.JS pages load).
3. Start Creo. Set the working directory to that folder: **File → Manage Session → Select Working Directory**.
4. Open `probe_creo.html` in Creo's built-in browser, the way you open your own Creo.JS pages.
5. Click **Run**. After about a minute the page says `Creo probe: N of M checks passed`.
6. Click **Download** (or select the text in the box and copy it) and send it to **Dutchy** in a Discord direct
   message.

The page makes `cfprobe_p`, `cfprobe_q` and `cfprobe_a` in that folder, saves them and exports STEP, then erases
them from the session again. Your own models are not opened or changed. Home folder names in the report are
replaced by `%USERPROFILE%`.

## What it checks

- The Creo releases installed (folders and the Windows uninstall list) and their version numbers.
- Which scripting is installed: the VB API (`pfcls`, registered with `vb_api_register.bat`), the Java files of
  Creo Object TOOLKIT Java / J-Link, Creo.JS, and Toolkit registration files.
- The VB API's own list of classes, members and enum values, read from its type library (`api.json`).
- In a Creo session of its own: create an empty part, add a parameter, save it, read its mass properties, export
  STEP, copy it, create an assembly, place the part in it, save and export that too, then end the session.
- Whether a sketched feature can be created through the VB API (PTC's reference lists `IpfcSolid.CreateFeature` as
  not implemented; the probe records Creo's own answer).

Every check is recorded as `ok` or `failed` with Creo's exact message, in `probe.log` and `probe.json`. A failed
check is a finding, not a problem with your Creo.

## Privacy

Your user name, PC name and home folder are replaced by `%USERNAME%`, `%COMPUTERNAME%` and `%USERPROFILE%` before
anything is written. Every file is scanned before it goes into the zip, and one that still contains your user or
PC name is left out (the log says which). The probe never opens your own files, never attaches to a Creo you have
open, and never changes `config.pro` or any other option file: options it needs are set for its own session only.

Native CAD files (.prt, .asm…) carry your Windows user and computer name inside them; we keep native files private and publish only STEP and files we've checked clean.

## If the VB API is not installed

The probe then says `pfcls.*AsyncConnection is not registered`. That is fine: send the zip anyway, it still tells us
which other scripting your Creo has. Adding the VB API needs the Creo installer and administrator rights, so only
do it if the PC is yours to change:

1. Run the Creo installer (PTC Installation Assistant) and choose **Reconfigure existing software**.
2. Select your Creo Parametric release, open **Customize**, and under the application features tick **VB API**
   (in some releases it is under **Creo Parametric → Customization**).
3. Finish the installer.
4. Open the release's `Parametric\bin` folder, right-click `vb_api_register.bat` and choose **Run as administrator**.
5. Run the probe again (steps 3 to 6 above).

## Source

The probe is generated from `builders/gen/creo_probe.ps1` by `builders/gen/emit_creo.py`; regenerate with
`python3 builders/gen/generate.py`. It uses only Windows, PowerShell and Creo's own public API.
