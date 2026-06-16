init -999 python:
    import renpy.store as store
    import renpy.exports as renpy
    import renpy.object as renpy_object
    import renpy.game as renpy_game
    import renpy.persistent as renpy_persistent_module
    import os
    import pickle
    import zlib
    import collections
    import collections.abc
    import struct
    import binascii
    import base64
    import time
    import datetime
    import builtins

    class CleanPersistent(object):
        """Spoofs renpy.persistent.Persistent"""
        def __setstate__(self, state):
            self.__dict__.update(state)
        def __getstate__(self):
            return self.__dict__

    class CleanNamespace(object):
        """Spoofs renpy.object.Object for generic containers"""
        def __setstate__(self, state):
            self.__dict__.update(state)
        def __getstate__(self):
            return self.__dict__
        def __repr__(self):
            return "<CleanNamespace %s>" % list(self.__dict__.keys())

    class CleanPreferences(object):
        """Spoofs renpy.preferences.Preferences"""
        def __setstate__(self, state):
            self.__dict__.update(state)
        def __getstate__(self):
            return self.__dict__

    CleanPersistent.__module__ = "renpy.persistent"
    CleanPersistent.__name__ = "Persistent"
    CleanPersistent.__qualname__ = "Persistent"

    CleanNamespace.__module__ = "renpy.object"
    CleanNamespace.__name__ = "Object"
    CleanNamespace.__qualname__ = "Object"

    CleanPreferences.__module__ = "renpy.preferences"
    CleanPreferences.__name__ = "Preferences"
    CleanPreferences.__qualname__ = "Preferences"

    def _hybrid_migration():
        import os
        import pickle
        import zlib
        import time
        import binascii
        import struct
        import base64
        import collections
        old_persistent_path = os.path.join(renpy.config.savedir, "persistent")
        migrated_marker_path = os.path.join(renpy.config.savedir, "persistent.migrated")

        if not os.path.exists(migrated_marker_path) and os.path.exists(old_persistent_path):
            print("Persistent Migration: Starting one-time migration from old persistent.")

            old_persistent = None
            try:
                with open(old_persistent_path, 'rb') as f:
                    old_persistent = pickle.loads(zlib.decompress(f.read()), encoding='latin1')
            except Exception as e:
                try: os.rename(old_persistent_path, old_persistent_path + ".corrupt")
                except Exception: pass

            if old_persistent:
                try:
                    EXCLUDED_ATTRIBUTES = {'_version', '_renpy_version', '_save_game_slots', '_location', '_game_menu_screen', '_main_menu_screen'}

                    for attr in dir(old_persistent):
                        if (attr.startswith('__') and attr.endswith('__')) or attr in EXCLUDED_ATTRIBUTES or callable(getattr(old_persistent, attr)):
                            continue
                        try:
                            value = getattr(old_persistent, attr)
                            setattr(store.persistent, attr, value)
                        except Exception: pass

                    renpy.save_persistent()

                    if not hasattr(store.persistent, "_mas_affection_version"):
                        store.persistent._mas_affection_version = 0

                    if store.persistent._mas_affection_version < 2:
                        try:
                            old_aff_data = getattr(store.persistent, "_mas_affection", {})
                            if old_aff_data is not None:
                                aff, today_exp, freeze_ts, apologyflag = 0.0, 0.0, time.time(), False

                                def _parse_to_int_float(val):
                                    try: return float(int(float(val))) if val is not None else 0.0
                                    except Exception: return 0.0

                                if isinstance(old_aff_data, dict):
                                    aff = _parse_to_int_float(old_aff_data.get("affection", 0.0))
                                    today_exp = _parse_to_int_float(old_aff_data.get("today_exp", 0.0))
                                    freeze_date = old_aff_data.get("freeze_date", None)
                                    apologyflag = old_aff_data.get("apologyflag", False)
                                elif hasattr(old_aff_data, 'affection'):
                                    aff = _parse_to_int_float(getattr(old_aff_data, 'affection', 0.0))
                                    today_exp = _parse_to_int_float(getattr(old_aff_data, 'today_exp', 0.0))
                                    freeze_date = getattr(old_aff_data, 'freeze_date', None)
                                    apologyflag = getattr(old_aff_data, 'apologyflag', False)
                                else:
                                    aff = _parse_to_int_float(old_aff_data)

                                if freeze_date is not None:
                                    try: freeze_ts = time.mktime(freeze_date.timetuple())
                                    except Exception: pass

                                if aff >= 1000000: aff = 0.0

                                v2_data = (aff, 0.0, today_exp, 0.0, float(freeze_ts), time.time(), 7.0)
                                packed_data = struct.pack("!d d d d d d d", *v2_data)
                                hex_data = binascii.hexlify(packed_data)
                                b64_data = base64.b64encode(hex_data).decode('ascii')

                                store.persistent._mas_affection_data = b64_data
                                store.persistent._mas_affection_should_apologise = apologyflag
                                store.persistent._mas_affection = collections.defaultdict(float)
                                store.persistent._mas_affection_version = 2
                                store.persistent._mas_v2_migration_done = True

                                try:
                                    if hasattr(store, 'mas_affection'):
                                        store.mas_affection._m1_script0x2daffection__runtime_backup = b64_data
                                except Exception: pass
                                renpy.save_persistent()
                        except Exception: pass

                    try:
                        with open(migrated_marker_path, 'w') as f: f.write("migrated")
                    except Exception: pass
                except Exception: pass

        print("Persistent Migration: Sanitizing persistent data for 6.99 compatibility...")

        original_persistent_cls = getattr(renpy_persistent_module, "Persistent", None)
        original_object_cls = getattr(renpy_object, "Object", None)

        new_persistent = CleanPersistent()

        RealList = builtins.list
        RealDict = builtins.dict
        RealSet = builtins.set

        memo = {}

        def _make_native(obj, path="root"):
            import datetime
            if obj is None or isinstance(obj, (int, float, bool, str, bytes,
                    datetime.date, datetime.time, datetime.datetime, datetime.timedelta)):
                return obj

            obj_id = id(obj)
            if obj_id in memo: return memo[obj_id]

            type_str = str(type(obj))

            # Fault-Tolerant Dict (Checked FIRST to avoid edge case overlapping)
            if "Dict" in type_str or "dict" in type_str or isinstance(obj, (dict, collections.abc.Mapping)):
                if hasattr(obj, 'items'):
                    new_dict = RealDict()
                    memo[obj_id] = new_dict
                    for k, v in obj.items():
                        try:
                            key_repr = str(k)
                            if len(key_repr) > 20: key_repr = key_repr[:17] + "..."
                            new_path = "%s[%s]" % (path, key_repr)
                            new_dict[_make_native(k, "%s.key" % new_path)] = _make_native(v, new_path)
                        except Exception: pass
                    return new_dict

            # Fault-Tolerant List
            if "List" in type_str or "list" in type_str or isinstance(obj, (list, collections.abc.Sequence)):
                if hasattr(obj, '__iter__') and not isinstance(obj, (set, tuple, str, bytes)):
                    new_list = RealList()
                    memo[obj_id] = new_list
                    for i, item in enumerate(obj):
                        try: new_list.append(_make_native(item, "%s[%d]" % (path, i)))
                        except Exception: new_list.append(None)
                    return new_list

            # Fault-Tolerant Set
            if "Set" in type_str or "set" in type_str or isinstance(obj, (set, frozenset, collections.abc.Set)):
                if hasattr(obj, '__iter__') and not isinstance(obj, (list, tuple, str, bytes)):
                    new_set = RealSet()
                    memo[obj_id] = new_set
                    for item in obj:
                        try: new_set.add(_make_native(item, "%s.{set_item}" % path))
                        except Exception: pass
                    return new_set

            # Fault-Tolerant Tuple
            if "Tuple" in type_str or "tuple" in type_str or isinstance(obj, tuple):
                res = []
                for idx, i in enumerate(obj):
                    try: res.append(_make_native(i, "%s[%d]" % (path, idx)))
                    except Exception: res.append(None)
                return builtins.tuple(res)

            # Fault-Tolerant Deque
            if "deque" in type_str or isinstance(obj, collections.deque):
                new_list = RealList()
                memo[obj_id] = new_list
                for i, item in enumerate(obj):
                    try: new_list.append(_make_native(item, "%s[%d]" % (path, i)))
                    except Exception: new_list.append(None)
                return new_list

            # Handle Objects
            new_obj = CleanPreferences() if ("Preferences" in type_str and "renpy.preferences" in type_str) else CleanNamespace()
            memo[obj_id] = new_obj
            attributes = {}

            if hasattr(obj, "__dict__"):
                for k, v in obj.__dict__.items(): attributes[k] = v

            if hasattr(obj, "__slots__"):
                for k in obj.__slots__:
                    if hasattr(obj, k): attributes[k] = getattr(obj, k)

            try:
                for k in dir(obj):
                    if k in attributes: continue
                    if k.startswith("__") and k.endswith("__"): continue
                    if k.startswith("_renpy"): continue
                    try:
                        v = getattr(obj, k)
                        if not callable(v): attributes[k] = v
                    except Exception: pass
            except Exception: pass

            if not attributes:
                lower_type = type_str.lower()
                if "renpy" in lower_type or "store" in lower_type or "revertable" in lower_type: return new_obj
                return obj

            for k, v in attributes.items():
                if (k.startswith('__') and k.endswith('__')) or callable(v) or k.startswith("_renpy"): continue
                try:
                    new_path = "%s.%s" % (path, k)
                    clean_k = _make_native(k, path + ".key_name")
                    clean_v = _make_native(v, new_path)
                    setattr(new_obj, clean_k, clean_v)
                except Exception: pass

            return new_obj

        try:
            print("Persistent Migration: Starting recursive sanitization...")

            # FIX: Use dir() instead of __dict__ to extract dynamically default variables
            # that were never explicitly saved to __dict__ in Py3!
            all_persistent_keys = dir(store.persistent)

            for k in all_persistent_keys:
                if (k.startswith("__") and k.endswith("__")) or k.startswith("_renpy"):
                    continue

                try:
                    v = getattr(store.persistent, k)
                    if callable(v):
                        continue

                    clean_val = _make_native(v, "persistent.%s" % k)

                    # ULTIMATE MOD FIX: If a variable looks like a mod DB and is missing/corrupted,
                    # absolutely force it to be an empty built-in python dictionary.
                    if clean_val is None or isinstance(clean_val, CleanNamespace):
                        if "_db" in k.lower() or "_dict" in k.lower() or "database" in k.lower():
                            clean_val = RealDict()

                    setattr(new_persistent, k, clean_val)
                except Exception as e:
                    pass

        except Exception as e:
            print("Persistent Migration: Outer error during sanitization: %s" % e)

        compat_persistent_path = os.path.join(renpy.config.savedir, "persistent_699")

        try:
            import renpy.preferences as renpy_preferences_module
            original_preferences_cls = getattr(renpy_preferences_module, "Preferences", None)

            if not original_preferences_cls:
                import sys
                p_module = sys.modules.get("renpy.preferences")
                if p_module and getattr(p_module, "Preferences", None):
                    original_preferences_cls = getattr(p_module, "Preferences", None)
                    renpy_preferences_module = p_module

            if original_persistent_cls: renpy_persistent_module.Persistent = CleanPersistent
            if original_object_cls: renpy_object.Object = CleanNamespace
            if original_preferences_cls: renpy_preferences_module.Preferences = CleanPreferences

            try:
                p_bytes = pickle.dumps(new_persistent, protocol=2)
                cdata = zlib.compress(p_bytes)
                with open(compat_persistent_path, "wb") as f:
                    f.write(cdata)

            except Exception as e:
                print("Persistent Migration: Failed to save compatible persistent file: %s" % e)

            finally:
                if original_persistent_cls: renpy_persistent_module.Persistent = original_persistent_cls
                if original_object_cls: renpy_object.Object = original_object_cls
                if original_preferences_cls: renpy_preferences_module.Preferences = original_preferences_cls

        except Exception:
            pass

        renpy.save_persistent()

    _hybrid_migration()
