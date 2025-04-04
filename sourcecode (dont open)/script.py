import threading
import shutil
import os
import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup

class SaveBackupTool(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.backup_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Schedule_I_Backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.header = Label(
            text="Save Backup Tool",
            font_size=24,
            bold=True,
            size_hint=(1, 0.15),
            color=(1, 1, 1, 1)
        )

        self.status_label = Label(
            text="Ready",
            font_size=16,
            size_hint=(1, 0.1),
            color=(0, 1, 0, 1)
        )

        self.btn_backup = Button(
            text="Create Backup",
            background_color=(0, 0, 1, 1),
            color=(1, 1, 1, 1),
            font_size=18,
            size_hint=(1, 0.1)
        )
        self.btn_backup.bind(on_press=self.create_backup)

        self.backup_list_scroll = ScrollView(size_hint=(1, 0.55))
        self.backup_list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.backup_list_layout.bind(minimum_height=self.backup_list_layout.setter('height'))
        self.backup_list_scroll.add_widget(self.backup_list_layout)

        self.add_widget(self.header)
        self.add_widget(self.status_label)
        self.add_widget(self.btn_backup)
        self.add_widget(self.backup_list_scroll)

        Clock.schedule_once(lambda dt: self.load_backup_list(), 1)

    def load_backup_list(self):
        self.backup_list_layout.clear_widgets()

        backups = sorted(os.listdir(self.backup_dir), reverse=True)
        if not backups:
            self.backup_list_layout.add_widget(Label(text="No backups found!", color=(1, 0, 0, 1)))
            return

        for backup_name in backups:
            full_path = os.path.join(self.backup_dir, backup_name)
            try:
                creation_time = os.path.getctime(full_path)
                creation_str = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')

                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)

                label = Label(
                    text=f"{backup_name} - {creation_str}",
                    size_hint_x=0.6,
                    color=(1, 1, 1, 1)
                )

                restore_btn = Button(
                    text="Restore",
                    size_hint_x=0.2,
                    background_color=(0, 0.5, 1, 1),
                    color=(1, 1, 1, 1)
                )
                restore_btn.bind(on_press=lambda inst, path=full_path: self.restore_specific_backup(path))

                delete_btn = Button(
                    text="Delete",
                    size_hint_x=0.2,
                    background_color=(1, 0, 0, 1),
                    color=(1, 1, 1, 1)
                )
                delete_btn.bind(on_press=lambda inst, path=full_path: self.confirm_delete(path))

                row.add_widget(label)
                row.add_widget(restore_btn)
                row.add_widget(delete_btn)

                self.backup_list_layout.add_widget(row)
            except Exception as e:
                self.backup_list_layout.add_widget(Label(text=f"Error reading {backup_name}", color=(1, 0, 0, 1)))

    def create_backup(self, instance):
        self.update_status("Creating backup...", (1, 1, 0, 1))
        threading.Thread(target=self._backup_task, daemon=True).start()

    def _backup_task(self):
        save_path = os.path.join(os.getenv('APPDATA'), '..', 'LocalLow', 'TVGS', 'Schedule I', 'saves')

        try:
            backup_name = f"backup_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            backup_path = os.path.join(self.backup_dir, backup_name)

            if os.path.isdir(save_path):
                shutil.copytree(save_path, backup_path, dirs_exist_ok=True)
            else:
                shutil.copy(save_path, backup_path)

            Clock.schedule_once(lambda dt: self.update_status("Backup Created!", (0, 1, 0, 1)), 0)
            Clock.schedule_once(lambda dt: self.load_backup_list(), 1)
        except Exception:
            Clock.schedule_once(lambda dt: self.update_status("Error during backup", (1, 0, 0, 1)), 0)

    def restore_specific_backup(self, backup_path):
        self.update_status("Restoring backup...", (1, 1, 0, 1))
        threading.Thread(target=self._restore_task, args=(backup_path,), daemon=True).start()

    def _restore_task(self, backup_path):
        save_path = os.path.join(os.getenv('APPDATA'), '..', 'LocalLow', 'TVGS', 'Schedule I', 'saves')

        try:
            if os.path.exists(save_path):
                shutil.rmtree(save_path)

            if os.path.isdir(backup_path):
                shutil.copytree(backup_path, save_path)
            else:
                shutil.copy(backup_path, save_path)

            Clock.schedule_once(lambda dt: self.update_status("Backup Restored!", (0, 1, 0, 1)), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"Error: {e}", (1, 0, 0, 1)), 0)

    def confirm_delete(self, path):
        content = BoxLayout(orientation='vertical', spacing=10)
        label = Label(text="Are you sure you want to delete this backup?")
        btns = BoxLayout(size_hint_y=None, height=40, spacing=5)

        yes = Button(text="Yes", background_color=(1, 0, 0, 1))
        no = Button(text="No")

        popup = Popup(title="Confirm Delete", content=content, size_hint=(0.7, 0.3))
        yes.bind(on_press=lambda x: (self.delete_backup(path), popup.dismiss()))
        no.bind(on_press=popup.dismiss)

        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(label)
        content.add_widget(btns)
        popup.open()

    def delete_backup(self, path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.update_status("Backup Deleted!", (1, 1, 0, 1))
            Clock.schedule_once(lambda dt: self.load_backup_list(), 1)
        except Exception as e:
            self.update_status(f"Delete Error: {e}", (1, 0, 0, 1))

    def update_status(self, message, color):
        self.status_label.text = message
        self.status_label.color = color

class BackupApp(App):
    def build(self):
        return SaveBackupTool()

if __name__ == "__main__":
    BackupApp().run()
