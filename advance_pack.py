"""
Bedrock Add-on Manifest Loader

Select a folder containing any resource pack and/or behavior pack

The program:
- Recursively finds manifest.json files
- Determines pack type
- Loads JSON data into strongly-typed dataclasses
- Stores results in variables for further processing
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json
import tkinter as tk
from tkinter import filedialog, messagebox


# ---------- Global Variables ----------

MAJOR: int = 1
MINOR: int = 2

# ---------- Dataclass Models ----------

@dataclass
class ManifestHeader:
        name: str
        description: str
        uuid: str
        version: list[int]
        min_engine_version: Optional[list[int]] = None


@dataclass
class Dependency:
        version: list[int] | str
        uuid: Optional[str] = None
        module_name: Optional[str] = None


@dataclass
class ModuleBase:
        type: str | None = None
        uuid: str | None = None
        version: list[int] | None = None
        description: Optional[str] = None


@dataclass
class ResourceModule(ModuleBase):
        type: str | None = None


@dataclass
class ClientDataModule(ModuleBase):
        type: str | None = None


@dataclass
class DataModule(ModuleBase):
        type: str | None = None


@dataclass
class ScriptModule(ModuleBase):
        type: str | None = None
        language: str | None = None
        entry: Optional[str] = None


@dataclass
class ResourcePack:
        format_version: int
        header: ManifestHeader
        modules: list[ResourceModule | ClientDataModule]
        dependencies: Optional[list[Dependency]] = None
        metadata: Optional[dict] = None


@dataclass
class BehaviorPack:
        format_version: int
        header: ManifestHeader
        modules: list[DataModule | ScriptModule]
        dependencies: Optional[list[Dependency]] = None
        metadata: Optional[dict] = None


# ---------- Loader Logic ----------

class ManifestLoader:
        """
        Discovers and loads BP/RP manifests into dataclasses.
        """

        def __init__(self, root: Path) -> None:

                self.root = root
                self.behavior_pack: Optional[BehaviorPack] = None
                self.resource_pack: Optional[ResourcePack] = None

                self.behavior_path: Optional[Path] = None
                self.resource_path: Optional[Path] = None



        def scan(self) -> None:
                for manifest_path in self.root.rglob("manifest.json"):
                        try:
                                self._load_manifest(manifest_path)
                        except Exception:
                                continue


        def _load_manifest(self, path: Path) -> None:
                with path.open("r", encoding="utf-8") as file:
                        data = json.load(file)

                modules = data.get("modules", [])

                for module in modules:
                        if module.get("type") == "data":
                                self.behavior_pack = self._load_behavior(data)
                                self.behavior_path = path
                                return

                        if module.get("type") in ("resources", "client_data"):
                                self.resource_pack = self._load_resource(data)
                                self.resource_path = path
                                return


        def _load_header(self, header: dict) -> ManifestHeader:
                return ManifestHeader(
                        name=header["name"],
                        description=header.get("description", ""),
                        uuid=header["uuid"],
                        version=header["version"],
                        min_engine_version=header.get("min_engine_version")
                )


        def _load_dependencies(self, dependencies: list[dict]) -> list[Dependency]:
                result: list[Dependency] = []

                for dep in dependencies:
                        result.append(Dependency(
                                version=dep["version"],
                                uuid=dep.get("uuid"),
                                module_name=dep.get("module_name")
                        ))
                return result


        def _load_behavior(self, data: dict) -> BehaviorPack:
                header = self._load_header(data["header"])

                modules: list[DataModule | ScriptModule] = []
                for module in data.get("modules", []):
                        if module["type"] == "data":
                                modules.append(DataModule(
                                        type=module["type"],
                                        uuid=module["uuid"],
                                        version=module["version"],
                                        description=module.get("description")
                                ))
                        elif module["type"] == "script":
                                modules.append(ScriptModule(
                                        type=module["type"],
                                        uuid=module["uuid"],
                                        version=module["version"],
                                        description=module.get("description"),
                                        language=module.get("language", "javascript"),
                                        entry=module.get("entry")
                                ))
                return BehaviorPack(
                        format_version=data.get("format_version", 2),
                        header=header,
                        modules=modules,
                        dependencies=self._load_dependencies(data.get("dependencies", [])) if "dependencies" in data else None,
                        metadata=data.get("metadata")
                )


        def _load_resource(self, data: dict) -> ResourcePack:
                header = self._load_header(data["header"])

                modules: list[ResourceModule | ClientDataModule] = []
                for module in data.get("modules", []):
                        if module["type"] == "resources":
                                modules.append(ResourceModule(
                                        type=module["type"],
                                        uuid=module["uuid"],
                                        version=module["version"],
                                        description=module.get("description")
                                ))
                        elif module["type"] == "client_data":
                                modules.append(ClientDataModule(
                                        type=module["type"],
                                        uuid=module["uuid"],
                                        version=module["version"],
                                        description=module.get("description")
                                ))
                return ResourcePack(
                        format_version=data.get("format_version", 2),
                        header=header,
                        modules=modules,
                        dependencies=self._load_dependencies(data.get("dependencies", [])) if "dependencies" in data else None,
                        metadata=data.get("metadata")
                )


# ---------- Tkinter UI ----------

class LoaderApp(tk.Tk):

        def __init__(self) -> None:

                super().__init__()
                self.title("Bedrock Manifest Loader")
                self.geometry("420x200")

                self.loader: Optional[ManifestLoader] = None

                tk.Button(self, text="Select Add-On Folder", command=self.select_folder).pack(pady=24)


        def select_folder(self) -> None:
                self.folder = filedialog.askdirectory(title="Select add-on folder")
                if not self.folder:
                        return

                self.loader = ManifestLoader(Path(self.folder))
                self.loader.scan()

                message = f"Resource Pack: {self.loader.resource_pack.header.name if self.loader.resource_pack else 'Not Found'}\nBehavior Pack: {self.loader.behavior_pack.header.name if self.loader.behavior_pack else 'Not Found'}"


                # messagebox.showinfo("Loaded", message)

                tk.Label(self, text=message).pack()

                tk.Button(self, text="Modify", command=self.open_modify).pack(pady=24)


        def open_modify(self) -> None:
                if self.loader is None:
                        return
                if self.loader.resource_pack is None and self.loader.behavior_pack is None:
                        messagebox.showerror("Error", "No Resource pack or Behavior pack loaded.")
                        return

                ModifyManifests(
                        self,
                        self.loader.resource_pack,
                        self.loader.behavior_pack,
                        self.loader
                )


class ModifyManifests(tk.Toplevel):

        def __init__(
                self,
                parent: tk.Misc,
                rp: ResourcePack | None,
                bp: BehaviorPack | None,
                loader: ManifestLoader
        ) -> None:
                super().__init__(parent)
                self.loader = loader
                self.geometry("800x500")

                if not rp and not bp:
                        self.destroy()
                        return

                self.title("Modify Manifest" if not (rp and bp) else "Modify Manifests")

                if rp:
                        self._add_pack_controls(
                                f"Resource Pack: {rp.header.name}",
                                rp,
                                bp
                        )

                if bp:
                        self._add_pack_controls(
                                f"Behavior Pack: {bp.header.name}",
                                bp,
                                rp
                        )

                self.status_var = tk.StringVar()
                self.status_label = tk.Label(self, textvariable=self.status_var, fg="green")
                self.status_label.pack(side="bottom", pady=8)

                tk.Button(self, text="Save Manifests", command=self._confirm_save).pack(pady=12)




        def _add_pack_controls(
                self,
                label: str,
                source: ResourcePack | BehaviorPack,
                target: ResourcePack | BehaviorPack | None
        ) -> None:
                tk.Label(self, text=label, pady=10).pack()

                tk.Button(
                        self,
                        text="Advance Minor Version",
                        command=lambda: self._advance_pack(source, target, MINOR)
                ).pack()

                tk.Button(
                        self,
                        text="Advance Major Version",
                        command=lambda: self._advance_pack(source, target, MAJOR)
                ).pack()


        def _advance_version(self, version: list[int], level: int) -> None:
                version[level] += 1
                if level == 1:
                        version[2] = 0


        def _advance_pack(
                self,
                source_pack: ResourcePack | BehaviorPack,
                target_pack: ResourcePack | BehaviorPack | None,
                level: int
        ) -> None:
                uuid = source_pack.header.uuid

                self._advance_version(source_pack.header.version, level)

                for module in source_pack.modules:
                        if module.type == ("data" or "resources") and module.version:
                                self._advance_version(module.version, level)

                if target_pack and target_pack.dependencies:
                        for dependency in target_pack.dependencies:
                                if dependency.uuid == uuid and isinstance(dependency.version, list):
                                        self._advance_version(dependency.version, level)

                pack_name = source_pack.header.name
                version = ".".join(map(str, source_pack.header.version))
                level_name = "Major" if level == MAJOR else "Minor"

                self._show_status(
                        f"{pack_name} {level_name} version advanced to {version}"
                )


        def _show_status(self, message: str, duration_ms: int = 3000) -> None:
                self.status_var.set(message)
                self.after(duration_ms, lambda: self.status_var.set(""))


        def _confirm_save(self) -> None:
                if not messagebox.askyesno(
                        "Confirm Save",
                        "Save changes to manifest.json files?"
                ):
                        return

                loader = self.loader

                if loader.resource_pack and loader.resource_path:
                        self._write_manifest(loader.resource_pack, loader.resource_path)

                if loader.behavior_pack and loader.behavior_path:
                        self._write_manifest(loader.behavior_pack, loader.behavior_path)

                self._show_status("Manifests saved successfully")


        def _strip_none(self, obj: dict) -> dict:
                return {k: v for k, v in obj.items() if v is not None}


        def _write_manifest(self, pack: ResourcePack | BehaviorPack, path: Path) -> None:
                data: dict = {
                        "format_version": pack.format_version,
                        "header": self._strip_none(vars(pack.header)),
                        "modules": [
                                self._strip_none(vars(m)) for m in pack.modules
                        ]
                }

                if pack.dependencies:
                        data["dependencies"] = [
                                self._strip_none(vars(d)) for d in pack.dependencies
                        ]

                if pack.metadata:
                        data["metadata"] = pack.metadata

                with path.open("w", encoding="utf-8") as file:
                        json.dump(data, file, indent=4)






if __name__ == "__main__":
        app = LoaderApp()
        app.mainloop()
