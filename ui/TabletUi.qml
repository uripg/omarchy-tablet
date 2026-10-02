import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Mpris

Item {
    id: root
    property var state: ({active:false, brightness:50, volume:50, muted:false})
    property bool expanded: false
    property bool promptsOpen: false
    readonly property color surface: "#171923"
    readonly property color raised: "#252936"
    readonly property color ink: "#cdd6f4"
    readonly property color muted: "#a6adc8"
    readonly property color accent: "#89b4fa"
    property string controller: ""
    readonly property var screen: Quickshell.screens.find(s => s.name === root.state.monitor) ?? Quickshell.screens[0]
    readonly property var player: {
        let candidates = Mpris.players.values.filter(p => (root.state.media_player === "any" || (p.identity + " " + p.desktopEntry + " " + p.dbusName).toLowerCase().includes((root.state.media_player || "brave").toLowerCase())));
        function score(p) {
            const url = String(p.metadata["xesam:url"] || "");
            return (url.includes("music.youtube.com") ? 100 : 0) + (p.isPlaying ? 10 : 0) + (p.trackTitle ? 1 : 0);
        }
        candidates.sort((a,b) => score(b)-score(a));
        return candidates.length ? candidates[0] : null;
    }
    readonly property string sourceName: player && String(player.metadata["xesam:url"] || "").includes("music.youtube.com") ? "YouTube Music" : "Brave"
    function command(args) { Quickshell.execDetached(args) }
    function control(action) { command([controller, action]) }
    function playback(action) {
        if (!player) return;
        if (action === "play" && player.canTogglePlaying) player.togglePlaying();
        if (action === "next" && player.canGoNext) player.next();
        if (action === "previous" && player.canGoPrevious) player.previous();
    }
    IpcHandler {
        target: "omarchy-tablet"
        function expand(): void { root.expanded = true }
        function collapse(): void { root.expanded = false }
        function media(): string { return JSON.stringify({player:root.player ? root.player.dbusName : null, title:root.player ? root.player.trackTitle : "", playing:root.player ? root.player.isPlaying : false}) }
        function playback(action: string): void { root.playback(action) }
    }
    FileView {
        path:Quickshell.env("XDG_RUNTIME_DIR") + "/omarchy-tablet/status.json"
        watchChanges:true
        printErrors:false
        onFileChanged:reload()
        onLoaded: {
            try {
                root.state=JSON.parse(text())
                if (!root.state.active) root.expanded=false
            } catch (e) { console.warn("Tablet Mode: invalid controller state") }
        }
    }
    component Icon: Image {
        property string name
        source: "icons/" + name + ".svg"
        sourceSize: Qt.size(24,24)
        width:24; height:24
    }
    component Action: Button {
        id: action
        property string symbol
        property string label
        property bool selected: false
        implicitHeight:56; implicitWidth:56
        Accessible.name: label
        hoverEnabled:true
        opacity: enabled ? 1 : .35
        scale: down ? .96 : 1
        ToolTip {
            visible: action.hovered && !action.down
            delay: 700
            text: action.label
            contentItem: Text { text:action.label; color:root.ink; font.pixelSize:13 }
            background: Rectangle { color:root.raised; radius:8; border.color:"#454b60" }
        }
        background: Rectangle { radius:16; color: action.down ? "#414b65" : action.selected ? "#34425d" : action.hovered ? "#303646" : "transparent"; border.width:action.visualFocus ? 2 : 0; border.color:root.accent }
        contentItem: Icon { name:action.symbol; horizontalAlignment:Image.AlignHCenter; verticalAlignment:Image.AlignVCenter; fillMode:Image.Pad }
        Behavior on scale { NumberAnimation { duration:100 } }
    }
    component TouchSlider: Slider {
        id: slider
        implicitHeight:52
        from:0; to:100; stepSize:1
        background: Rectangle {
            x:slider.leftPadding; y:(slider.height-height)/2
            width:slider.availableWidth; height:8; radius:4; color:"#353b4d"
            Rectangle { width:slider.visualPosition*parent.width; height:parent.height; radius:4; color:root.accent }
        }
        handle: Rectangle {
            x:slider.leftPadding+slider.visualPosition*(slider.availableWidth-width); y:(slider.height-height)/2
            width:28; height:28; radius:14; color:slider.pressed ? "#ffffff" : root.ink
            border.color:root.surface; border.width:3
        }
    }
    component Playback: RowLayout {
        spacing:8
        Action { symbol:"previous"; label:"Previous track"; enabled:!!root.player && root.player.canGoPrevious; onClicked:root.playback("previous") }
        Action { symbol:root.player && root.player.isPlaying ? "pause" : "play"; label:root.player && root.player.isPlaying ? "Pause" : "Play"; selected:true; enabled:!!root.player && root.player.canTogglePlaying; onClicked:root.playback("play") }
        Action { symbol:"next"; label:"Next track"; enabled:!!root.player && root.player.canGoNext; onClicked:root.playback("next") }
    }
    PanelWindow {
        id:dock
        screen:root.screen
        visible:root.state.active && !root.state.zen
        anchors { top:true }
        margins.top:12
        implicitWidth:Math.min(root.screen.width-64, root.player ? 1064 : 744)
        implicitHeight:76
        exclusiveZone:88
        color:"transparent"
        WlrLayershell.namespace:"omarchy-tablet-controls"
        WlrLayershell.layer:WlrLayer.Top
        WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
        Rectangle {
            anchors.fill:parent; radius:24; color:root.surface; border.color:"#34394b"
            RowLayout {
                anchors.fill:parent; anchors.margins:10; spacing:4
                Action { symbol:"apps"; label:"Applications"; onClicked:root.command(["omarchy-menu","toggle","apps"]) }
                Action { symbol:"keyboard"; label:"Show or hide keyboard"; onClicked:root.control("keyboard") }
                Rectangle { Layout.preferredWidth:1; Layout.preferredHeight:28; color:"#34394b" }
                Action { symbol:"left"; label:"Previous workspace"; onClicked:root.command(["hyprctl","dispatch",'hl.dsp.focus({workspace="e-1"})']) }
                Action { symbol:"right"; label:"Next workspace"; onClicked:root.command(["hyprctl","dispatch",'hl.dsp.focus({workspace="e+1"})']) }
                Item { Layout.fillWidth:true; visible:!root.player }
                ColumnLayout {
                    visible:!!root.player; Layout.fillWidth:true; spacing:3
                    Text { Layout.fillWidth:true; textFormat:Text.PlainText; text:root.player ? root.player.trackTitle || "Media in Brave" : ""; color:root.ink; font.pixelSize:15; font.weight:Font.DemiBold; elide:Text.ElideRight }
                    Text { Layout.fillWidth:true; textFormat:Text.PlainText; text:root.player ? root.player.trackArtist || root.sourceName : ""; color:root.muted; font.pixelSize:12; elide:Text.ElideRight }
                }
                Action { visible:!!root.player; symbol:root.player && root.player.isPlaying ? "pause" : "play"; label:"Play or pause"; enabled:!!root.player && root.player.canTogglePlaying; onClicked:root.playback("play") }
                Action { symbol:"rotate"; label:"Rotate display"; onClicked:root.control("rotate") }
                Action { symbol:"book"; label:"Enter Zen reading mode"; onClicked:root.control("zen-on") }
                Action { symbol:"settings"; label:"Quick controls"; selected:root.expanded; onClicked:root.expanded=!root.expanded }
                Rectangle { Layout.preferredWidth:1; Layout.preferredHeight:28; color:"#34394b" }
                Action {
                    id: closeWindow
                    symbol:"close"; label:"Close focused window"; implicitWidth:100
                    onClicked:root.command(["hyprctl","repl","hl.dispatch(hl.dsp.window.close())"])
                    background:Rectangle {
                        radius:16
                        color:closeWindow.down ? "#643948" : closeWindow.hovered ? "#49303e" : "#352630"
                        border.width:closeWindow.visualFocus ? 2 : 0
                        border.color:"#f38ba8"
                    }
                    contentItem:Item {
                        Row {
                            anchors.centerIn:parent; spacing:8
                            Icon { name:"close" }
                            Text { text:"Close"; color:"#f38ba8"; font.pixelSize:15; height:24; verticalAlignment:Text.AlignVCenter }
                        }
                    }
                }
            }
        }
    }
    PanelWindow {
        screen:root.screen
        visible:root.state.active && !root.state.zen && root.expanded
        anchors { top:true; right:true }
        margins { top:100; right:48 }
        implicitWidth:420; implicitHeight:Math.min(content.implicitHeight+40, root.screen.height-120)
        exclusionMode:ExclusionMode.Ignore
        color:"transparent"
        WlrLayershell.namespace:"omarchy-tablet-panel"
        WlrLayershell.layer:WlrLayer.Overlay
        WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
        Rectangle {
            anchors.fill:parent; radius:28; color:root.surface; border.color:"#34394b"
            Flickable {
                id:controlScroll
                anchors.fill:parent; anchors.margins:20
                contentHeight:content.implicitHeight
                clip:true
                boundsBehavior:Flickable.StopAtBounds
                ScrollBar.vertical:ScrollBar { policy:ScrollBar.AsNeeded }
            ColumnLayout {
                id:content
                width:controlScroll.width
                spacing:16
                RowLayout {
                    Text { text:"Quick controls"; color:root.ink; font.pixelSize:22; font.weight:Font.DemiBold; Layout.fillWidth:true }
                    Action { symbol:"close"; label:"Close controls"; onClicked:root.expanded=false }
                }
                Rectangle {
                    Layout.fillWidth:true; implicitHeight:musicContent.implicitHeight+32; radius:20; color:root.raised
                    ColumnLayout {
                        id:musicContent
                        anchors { left:parent.left; right:parent.right; top:parent.top; margins:16 } spacing:12
                        RowLayout {
                            spacing:14
                            Rectangle {
                                width:64; height:64; radius:12; color:"#34394b"; clip:true
                                Icon { anchors.centerIn:parent; name:"music" }
                                Image { anchors.fill:parent; source:root.player ? root.player.trackArtUrl : ""; fillMode:Image.PreserveAspectCrop; asynchronous:true; visible:status===Image.Ready }
                            }
                            ColumnLayout {
                                Layout.fillWidth:true; spacing:4
                                Text { textFormat:Text.PlainText; text:root.player ? root.sourceName + (root.player.isPlaying ? " · Playing" : " · Paused") : "YouTube Music"; color:root.accent; font.pixelSize:12 }
                                Text { Layout.fillWidth:true; textFormat:Text.PlainText; text:root.player ? root.player.trackTitle || "Media in Brave" : "Ready when you are"; color:root.ink; font.pixelSize:17; font.weight:Font.DemiBold; elide:Text.ElideRight }
                                Text { Layout.fillWidth:true; textFormat:Text.PlainText; text:root.player ? root.player.trackArtist : "Play a song in Brave"; color:root.muted; font.pixelSize:13; elide:Text.ElideRight }
                            }
                        }
                        Playback { Layout.alignment:Qt.AlignHCenter; visible:!!root.player }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth:true; spacing:0
                    RowLayout {
                        Icon { name:"sun" }
                        Text { text:root.state.backlight ? "Brightness" : "Brightness unavailable"; color:root.ink; font.pixelSize:15; Layout.fillWidth:true }
                        Text { text:Math.round(brightness.value)+"%"; color:root.muted; font.pixelSize:14 }
                    }
                    TouchSlider {
                        id:brightness; Layout.fillWidth:true; from:5; enabled:!!root.state.backlight
                        Binding { target:brightness; property:"value"; value:root.state.brightness || 0; when:!brightness.pressed }
                        onMoved:brightnessApply.restart()
                        onPressedChanged:if (!pressed) { brightnessApply.stop(); root.command(["brightnessctl","-d",root.state.backlight,"set",Math.round(value)+"%"]) }
                        Timer { id:brightnessApply; interval:60; onTriggered:root.command(["brightnessctl","-d",root.state.backlight,"set",Math.round(brightness.value)+"%"]) }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth:true; spacing:0
                    RowLayout {
                        Action { symbol:root.state.muted ? "muted" : "volume"; label:root.state.muted ? "Unmute" : "Mute"; implicitWidth:48; implicitHeight:48; onClicked:root.command(["wpctl","set-mute","@DEFAULT_AUDIO_SINK@","toggle"]) }
                        Text { text:root.state.muted ? "Volume · Muted" : "Volume"; color:root.ink; font.pixelSize:15; Layout.fillWidth:true }
                        Text { text:Math.round(volume.value)+"%"; color:root.muted; font.pixelSize:14 }
                    }
                    TouchSlider {
                        id:volume; Layout.fillWidth:true
                        Binding { target:volume; property:"value"; value:root.state.volume; when:!volume.pressed }
                        onMoved:volumeApply.restart()
                        onPressedChanged:if (!pressed) { volumeApply.stop(); root.command(["wpctl","set-volume","@DEFAULT_AUDIO_SINK@",Math.round(value)+"%"]) }
                        Timer { id:volumeApply; interval:60; onTriggered:root.command(["wpctl","set-volume","@DEFAULT_AUDIO_SINK@",Math.round(volume.value)+"%"]) }
                    }
                }
                Rectangle { Layout.fillWidth:true; implicitHeight:1; color:"#34394b" }
                Text { visible:!!root.state.error; text:root.state.error || ""; color:"#f9e2af"; font.pixelSize:13; Layout.fillWidth:true; wrapMode:Text.WordWrap }
                Text { text:"Zen reading"; color:root.ink; font.pixelSize:18; font.weight:Font.DemiBold }
                Text { text:"Hide the controls. Keep just one restore button."; color:root.muted; font.pixelSize:13; Layout.fillWidth:true; wrapMode:Text.WordWrap }
                RowLayout {
                    Layout.fillWidth:true; spacing:8
                    Repeater {
                        model:[{label:"Grayscale",key:"gray"},{label:"Warm light",key:"warm"}]
                        delegate:Button {
                            required property var modelData
                            Layout.fillWidth:true; implicitHeight:56
                            Accessible.name:modelData.label
                            background:Rectangle { radius:14; color:root.state[modelData.key] ? "#34425d" : root.raised }
                            contentItem:Text { text:modelData.label + (root.state[modelData.key] ? " · On" : " · Off"); color:root.ink; font.pixelSize:14; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter }
                            onClicked:root.control("reading-"+modelData.key)
                        }
                    }
                }
                Text { text:"Filters apply in Zen; your colors return when you leave."; color:root.muted; font.pixelSize:12; Layout.fillWidth:true; wrapMode:Text.WordWrap }
                Button {
                    Layout.fillWidth:true; implicitHeight:54
                    Accessible.name:"Enter Zen reading mode"
                    background:Rectangle { radius:14; color:parent.down ? "#526887" : "#34425d" }
                    contentItem:Text { text:"Enter Zen"; color:root.ink; font.pixelSize:16; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter }
                    onClicked: { root.expanded=false; root.control("zen-on") }
                }
                RowLayout {
                    Layout.fillWidth:true
                    Repeater {
                        model:[{label:"Landscape",command:"landscape"},{label:"Portrait left",command:"portrait"},{label:"Portrait right",command:"portrait-right"}]
                        delegate:Button {
                            required property var modelData
                            Layout.fillWidth:true; implicitHeight:52
                            text:modelData.label; font.pixelSize:13
                            background:Rectangle { radius:12; color:parent.down ? "#414b65" : root.raised }
                            contentItem:Text { text:parent.text; color:root.ink; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter }
                            onClicked:root.control(modelData.command)
                        }
                    }
                }
                Rectangle { Layout.fillWidth:true; implicitHeight:1; color:"#34394b" }
                Button {
                    Layout.fillWidth:true; implicitHeight:52
                    Accessible.name:"Return to desktop mode"
                    background:Rectangle { radius:14; color:parent.down ? "#34394b" : root.raised }
                    contentItem:Text { text:"Return to desktop"; color:root.ink; font.pixelSize:15; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter }
                    onClicked:root.control("off")
                }
            }
            }
        }
    }
    // A non-focusing strip above the keyboard, so taps still type into the app.
    PanelWindow {
        screen:root.screen
        visible:root.state.active && !root.state.zen && !!root.state.keyboard_visible
        anchors { bottom:true; left:true; right:true }
        margins.bottom:root.state.keyboard_height || 400
        implicitHeight:root.promptsOpen ? 138 : 66
        exclusionMode:ExclusionMode.Ignore
        color:root.surface
        WlrLayershell.namespace:"tablet-writing-strip"
        WlrLayershell.layer:WlrLayer.Overlay
        WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
        component Chip: Button {
            implicitHeight:50; implicitWidth:110
            font.pixelSize:16
            background:Rectangle { radius:12; color:parent.down ? "#414b65" : root.raised }
            contentItem:Text { text:parent.text; color:root.ink; font:parent.font; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter; elide:Text.ElideRight }
        }
        ColumnLayout {
            anchors.fill:parent; anchors.margins:8; spacing:12
            RowLayout {
                spacing:8
                Chip { text:(root.state.language || "en").toUpperCase(); implicitWidth:64; Accessible.name:"Switch suggestion language"; onClicked:root.control("language") }
                Chip { text:root.state.words ? "Words on" : "Words off"; onClicked:root.control("words") }
                Repeater {
                    model:root.state.suggestions || []
                    delegate:Chip {
                        required property string modelData
                        Layout.fillWidth:true
                        text:modelData
                        onClicked:root.control("complete:"+modelData)
                    }
                }
                Text { visible:!(root.state.suggestions || []).length; Layout.fillWidth:true; text:root.state.words ? "Type a word · Hold a letter for variants" : "Word suggestions paused"; color:root.muted; font.pixelSize:14; elide:Text.ElideRight }
                Chip { text:root.promptsOpen ? "Hide prompts" : "Prompts"; implicitWidth:140; onClicked:root.promptsOpen=!root.promptsOpen }
            }
            RowLayout {
                visible:root.promptsOpen; spacing:8
                Repeater {
                    model:[{name:"Explain",id:"explain"},{name:"Fix",id:"fix"},{name:"Review",id:"review"},{name:"Rewrite",id:"rewrite"},{name:"Plan",id:"plan"},{name:"Continue",id:"continue"}]
                    delegate:Chip {
                        required property var modelData
                        Layout.fillWidth:true
                        text:modelData.name
                        onClicked: { root.control("prompt:"+modelData.id); root.promptsOpen=false }
                    }
                }
            }
        }
    }

    PanelWindow {
        screen:root.screen
        visible:root.state.active && !!root.state.zen
        anchors { bottom:true; right:true }
        margins { bottom:18; right:18 }
        implicitWidth:58; implicitHeight:58
        exclusionMode:ExclusionMode.Ignore
        color:"transparent"
        WlrLayershell.namespace:"tablet-zen-restore"
        WlrLayershell.layer:WlrLayer.Overlay
        WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
        Action {
            anchors.fill:parent
            symbol:"book"; label:"Leave Zen and restore controls"
            background:Rectangle { radius:29; color:parent.down ? "#414b65" : "#cc171923"; border.color:"#70778a"; border.width:1 }
            onClicked:root.control("zen-off")
        }
    }

}
