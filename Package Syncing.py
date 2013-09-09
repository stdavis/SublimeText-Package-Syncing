import sublime, sublime_plugin

import fnmatch, os.path, logging, time
logging.basicConfig(level = logging.INFO, format="[%(asctime)s - %(levelname)s - %(name)s] %(message)s")

try:
	from .package_syncing import tools
except ValueError:
	from package_syncing import tools


class PkgSyncEnableCommand(sublime_plugin.WindowCommand):

	def is_enabled(self):
		s = sublime.load_settings("Package Syncing.sublime-settings")
		return not s.get("sync", False)

	def run(self):
		s = sublime.load_settings("Package Syncing.sublime-settings")
		s.set("sync", True)
		sublime.save_settings("Package Syncing.sublime-settings")
		
		# Start watcher
		tools.start_watcher()


class PkgSyncDisableCommand(sublime_plugin.WindowCommand):

	def is_enabled(self):
		s = sublime.load_settings("Package Syncing.sublime-settings")
		return s.get("sync", False)

	def run(self):
		s = sublime.load_settings("Package Syncing.sublime-settings")
		s.set("sync", False)
		sublime.save_settings("Package Syncing.sublime-settings")

		# Stop watcher
		tools.stop_watcher()


class PkgSyncCommand(sublime_plugin.ApplicationCommand):

	def is_enabled(self):
		s = sublime.load_settings("Package Syncing.sublime-settings")
		return s.get("sync", False) and s.get("sync_folder") != None

	def run(self, mode = ["pull", "push"], override = False):
		
		# Stop watcher and wait for the poll
		tools.stop_watcher()
		time.sleep(1.5)
		
		if "pull" in mode:
			tools.pull_all(override)
		if "push" in mode:
			tools.push_all(override)
		
		# Restart watcher again
		tools.start_watcher()


class PkgSyncFolderCommand(sublime_plugin.WindowCommand):

	def run(self):
		# Load settings to provide an initial value for the input panel
		s = sublime.load_settings("Package Syncing.sublime-settings")
		sync_folder = s.get("sync_folder")

		# Suggest user dir if nothing set or folder do not exists
		if not sync_folder or not os.path.isdir(sync_folder):
			sync_folder = os.path.expanduser("~")

		def on_done(path):
			if not os.path.isdir(path):
				os.makedirs(path)

			if os.path.isdir(path):
				if os.listdir(path):
					if sublime.ok_cancel_dialog("The selected folder is not empty, would you like to continue and override your local settings?", "Continue"):
						override = True
					else:
						self.window.show_input_panel("Sync Folder", path, on_done, None, None)
						return
				else:
					override = False

				# Adjust settings
				s.set("sync", True)
				s.set("sync_folder", path)

				# Reset last-run file
				file_path = os.path.join(sublime.packages_path(), "User", "Package Syncing.last-run")
				if os.path.isfile(file_path):
					os.remove(file_path)

				sublime.save_settings("Package Syncing.sublime-settings")
				sublime.status_message("sync_folder successfully set to \"%s\"" % path)
				#
				sublime.run_command("pkg_sync", {"mode": ["pull", "push"], "override": True})
			else:
				sublime.error_message("Invalid Path %s" % path)

		self.window.show_input_panel("Sync Folder", sync_folder, on_done, None, None)


def plugin_loaded():
	tools.pull_all()
	tools.push_all()
	tools.start_watcher()

def plugin_unloaded():
	tools.stop_watcher()

if sublime.version()[0] == "2":
	plugin_loaded()
