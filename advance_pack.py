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
        type: str
        uuid: str
        version: list[int]
        description: Optional[str] = None


@dataclass
class ResourceModule(ModuleBase):
        type: str = field(init=False, default="resources")


@dataclass
class ClientDataModule(ModuleBase):
        type: str = field(init=False, default="client_data")


@dataclass
class DataModule(ModuleBase):
        type: str = field(init=False, default="data")


@dataclass
class ScriptModule(ModuleBase):
        type: str = field(init=False, default="script")
        language: str = "javascript"
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
                                return
                        if module.get("type") in ("resources", "client_data"):
                                self.resource_pack = self._load_resource(data)
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
                                        uuid=module["uuid"],
                                        version=module["version"],
                                        description=module.get("description")
                                ))
                        elif module["type"] == "script":
                                modules.append(ScriptModule(
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
                                        uuid=module["uuid"],
                                        version=module["version"],
                                        description=module.get("description")
                                ))
                        elif module["type"] == "client_data":
                                modules.append(ClientDataModule(
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

                message = f"Behavior Pack: {self.loader.behavior_pack.header.name if self.loader.behavior_pack else 'Not Found'}\nResource Pack: {self.loader.resource_pack.header.name if self.loader.resource_pack else 'Not Found'}"


                messagebox.showinfo("Loaded", message)

                tk.Label(self, text=message).pack()

                tk.Button(self, text="Modify", command=self.open_modify).pack(pady=24)

        def open_modify(self) -> None:
                if self.loader is None:
                        return
                if self.loader.resource_pack is None and self.loader.behavior_pack is None:
                        messagebox.showerror("Error", "No Resource pack or Behavior pack loaded.")
                        return

                ModifyManifests(self.loader.resource_pack, self.loader.behavior_pack)

class ModifyManifests(tk.Toplevel):

        def __init__(self, rp_data: ResourcePack | None, bp_data: BehaviorPack | None) -> None:
                super().__init__()
                self.title("Modify Manifests")
                self.geometry("800x500")



if __name__ == "__main__":
        app = LoaderApp()
        app.mainloop()
