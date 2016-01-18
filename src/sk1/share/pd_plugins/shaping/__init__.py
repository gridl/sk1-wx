# -*- coding: utf-8 -*-
#
# 	Copyright (C) 2016 by Igor E. Novikov
#
# 	This program is free software: you can redistribute it and/or modify
# 	it under the terms of the GNU General Public License as published by
# 	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful,
# 	but WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 	GNU General Public License for more details.
#
# 	You should have received a copy of the GNU General Public License
# 	along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os, wal

from uc2.formats.sk2 import sk2_const
from uc2.libgeom import apply_trafo_to_paths
from uc2.libgeom import intersect_paths, fuse_paths, trim_paths, excluse_paths

from sk1 import _, events
from sk1.dialogs import msg_dialog
from sk1.resources import icons, get_icon, get_bmp
from sk1.app_plugins import RS_Plugin

PLG_DIR = __path__[0]
IMG_DIR = os.path.join(PLG_DIR, 'images')

def make_artid(name):
	return os.path.join(IMG_DIR, name + '.png')

def get_plugin(app):
	return Shaping_Plugin(app)

PLUGIN_ICON = make_artid('icon')

TRIM_MODE = 0
INTERSECTION_MODE = 1
EXCLUSION_MODE = 2
FUSION_MODE = 3

SHAPING_MODES = [TRIM_MODE, INTERSECTION_MODE, EXCLUSION_MODE, FUSION_MODE]

SHAPING_MODE_ICONS = {
TRIM_MODE:icons.PD_PATHS_TRIM,
INTERSECTION_MODE:icons.PD_PATHS_INTERSECTION,
EXCLUSION_MODE:icons.PD_PATHS_EXCLUSION,
FUSION_MODE:icons.PD_PATHS_FUSION,
}

SHAPING_MODE_NAMES = {
TRIM_MODE:_('Trim'),
INTERSECTION_MODE:_('Intersection'),
EXCLUSION_MODE:_('Exclusion'),
FUSION_MODE:_('Fusion'),
}

SHAPING_MODE_PICS = {
TRIM_MODE:make_artid('shaping-trim'),
INTERSECTION_MODE:make_artid('shaping-intersection'),
EXCLUSION_MODE:make_artid('shaping-exclusion'),
FUSION_MODE:make_artid('shaping-fusion'),
}


class AbstractShapingPanel(wal.VPanel):

	pid = TRIM_MODE
	app = None
	obj_num = 2

	def __init__(self, parent, app):
		wal.VPanel.__init__(self, parent)
		self.app = app

		self.pack(wal.Label(self, SHAPING_MODE_NAMES[self.pid], fontbold=True))

		self.pic_panel = wal.VPanel(self, border=True)
		self.pic_panel.set_bg(wal.WHITE)
		self.bmp = get_bmp(self.pic_panel, SHAPING_MODE_PICS[self.pid])
		self.pic_panel.pack(self.bmp, padding_all=5)
		self.pack(self.pic_panel, padding=10)

		self.del_check = wal.Checkbox(self, _('Delete originals'))
		self.pack(self.del_check)

		txt = _('Apply')
		if self.pid == TRIM_MODE: txt = _('Apply to...')
		self.apply_btn = wal.Button(self, txt, onclick=self.action)
		self.pack(self.apply_btn, fill=True, padding_all=5)

	def set_enable(self, value):
		self.del_check.set_enable(value)
		self.apply_btn.set_enable(value)
		self.pic_panel.set_enable(value)
		self.bmp.set_enable(value)

	def get_sel_count(self):
		doc = self.app.current_doc
		return len(doc.selection.objs)

	def get_selection(self):
		doc = self.app.current_doc
		objs = [] + doc.selection.objs
		if not self.check_selection(objs):
			msg = _('Selection contains objects, that cannot used for this operation')
			msg_dialog(self.app.mw, self.app.appdata.app_name, msg)
			objs = []
		return objs

	def check_selection(self, sel):
		ret = True
		for obj in sel:
			if not obj.is_primitive():
				ret = False
		return ret

	def get_paths_list(self, objs):
		paths_list = []
		for obj in objs:
			paths = apply_trafo_to_paths(obj.get_initial_paths(), obj.trafo)
			paths_list.append(paths)
		return paths_list

	def update(self):
		if self.get_sel_count() >= self.obj_num:
			self.set_enable(True)
		else:
			self.set_enable(False)

	def action(self):pass


class TrimPanel(AbstractShapingPanel):

	pid = TRIM_MODE
	obj_num = 1

	def action(self):pass

class IntersectionPanel(AbstractShapingPanel):

	pid = INTERSECTION_MODE

	def action(self):pass

class ExclusionPanel(AbstractShapingPanel):

	pid = EXCLUSION_MODE

	def action(self):pass

class FusionPanel(AbstractShapingPanel):

	pid = FUSION_MODE

	def action(self):pass


SHAPING_CLASSES = {
TRIM_MODE:TrimPanel,
INTERSECTION_MODE:IntersectionPanel,
EXCLUSION_MODE:ExclusionPanel,
FUSION_MODE:FusionPanel,
}

class Shaping_Plugin(RS_Plugin):

	pid = 'ShapingPlugin'
	name = 'Shaping'
	active_panel = None
	panels = {}

	def build_ui(self):
		self.icon = get_icon(PLUGIN_ICON)
		self.panel.pack((5, 5))
		self.shaping_keeper = wal.HToggleKeeper(self.panel, SHAPING_MODES,
							SHAPING_MODE_ICONS,
							SHAPING_MODE_NAMES, self.on_mode_change)
		self.panel.pack(self.shaping_keeper)
		self.panel.pack(wal.HLine(self.panel), fill=True, padding=3)

		self.shaping_panel = wal.VPanel(self.panel)

		self.panels = {}
		for item in SHAPING_MODES:
			panel = SHAPING_CLASSES[item](self.shaping_panel, self.app)
			panel.hide()
			self.panels[item] = panel

		self.panel.pack(self.shaping_panel, fill=True, padding_all=5)
		self.panel.pack(wal.HLine(self.panel), fill=True)

		events.connect(events.DOC_CHANGED, self.update)
		events.connect(events.SELECTION_CHANGED, self.update)
		events.connect(events.DOC_MODIFIED, self.update)
		self.update()

	def update(self, *args):
		if self.active_panel:
			self.active_panel.update()

	def on_mode_change(self, mode):
		if self.active_panel:
			self.active_panel.hide()
			self.shaping_panel.remove(self.active_panel)
		self.active_panel = self.panels[mode]
		self.shaping_panel.pack(self.active_panel, fill=True)
		self.active_panel.show()
		self.panel.layout()
		self.update()

	def show_signal(self, mode=TRIM_MODE, *args):
		self.shaping_keeper.set_mode(mode)
		self.on_mode_change(mode)
