#!/usr/bin/env python
import sys
import os
import uuid
import subprocess
import lxml.etree as ET
from ififuncs import get_date_modified
from premis import make_agent
from premis import write_premis
from premis import setup_xml
from premis import create_intellectual_entity
from premis import create_unit
from premis import get_input
from premis import representation_uuid_csv


def create_representation(
        premisxml, premis_namespace, doc, premis,
        items, linkinguuids, representation_uuid,
        sequence, intellectual_entity_uuid
        ):
        object_parent = create_unit(
            1, premis, 'object'
            )
        object_identifier_parent = create_unit(
            1, object_parent, 'objectIdentifier'
            )
        object_identifier_uuid = create_unit(
            0, object_parent, 'objectIdentifier'
            )
        object_identifier_uuid_type = create_unit(
            1, object_identifier_uuid, 'objectIdentifierType'
            )
        object_identifier_uuid_type.text = 'UUID'
        object_identifier_uuid_value = create_unit(
            2, object_identifier_uuid, 'objectIdentifierValue'
            )
        object_identifier_uuid_value.text = representation_uuid
        # add uuids to csv so that other workflows can use them as linking identifiers.
        representation_uuid_csv(
            items['filmographic'], items['sourceAccession'], representation_uuid
            )
        object_parent.insert(
            1, object_identifier_parent
            )
        ob_id_type = ET.Element("{%s}objectIdentifierType" % (premis_namespace))
        ob_id_type.text = 'Irish Film Archive Object Entry Register'
        objectIdentifierValue = create_unit(
            1, object_identifier_parent, 'objectIdentifierValue'
            )
        objectIdentifierValue.text = items['oe']
        object_identifier_parent.insert(
            0, ob_id_type
            )
        objectCategory = create_unit(
            2, object_parent, 'objectCategory'
            )
        objectCategory.text = 'representation'
        # These hardcoded relationships do not really belong here. They should be stipulated by another microservice
        if sequence == 'sequence':
            representation_relationship(
                object_parent, premisxml, items,
                'structural', 'has root', linkinguuids[1][0],
                'root_sequence', 'UUID'
                )
            for i in linkinguuids[1]:
                representation_relationship(
                    object_parent, premisxml, items, 'structural',
                    'includes', i, 'includes', 'UUID'
                    )
        representation_relationship(
            object_parent, premisxml, items, 'structural',
            'includes',linkinguuids[0], 'n/a', 'UUID'
            )
        representation_relationship(
            object_parent, premisxml, items, 'derivation',
            'has source',linkinguuids[2], 'n/a',
            'Irish Film Archive Film Accession Register 2010 -'
            )
        representation_relationship(
            object_parent, premisxml, items,
            'structural', 'represents', intellectual_entity_uuid, 'n/a', 'UUID'
            )
        return object_parent

def representation_relationship(
        object_parent, premisxml, items, relationshiptype,
        relationshipsubtype, linking_identifier, root_sequence, linkingtype
    ):
        relationship = create_unit(
            -1, object_parent, 'relationship'
            )
        representationrelatedObjectIdentifier = create_unit(
            2, relationship, 'relatedObjectIdentifier'
            )
        representationrelatedObjectIdentifierType = create_unit(
            2, representationrelatedObjectIdentifier,
            'relatedObjectIdentifierType'
            )
        representationrelatedObjectIdentifierValue = create_unit(
            3, representationrelatedObjectIdentifier,
            'relatedObjectIdentifierValue'
            )
        if root_sequence == 'root_sequence':
            relatedObjectSequence = create_unit(
                4, relationship, 'relatedObjectSequence'
                )
            relatedObjectSequence.text = '1'
        relationshipType = create_unit(
            0, relationship, 'relationshipType'
            )
        relationshipType.text = relationshiptype
        relationshipSubType = create_unit(
            1, relationship, 'relationshipSubType'
            )
        relationshipSubType.text = relationshipsubtype
        representationrelatedObjectIdentifierType.text = linkingtype
        representationrelatedObjectIdentifierValue.text = linking_identifier


def create_object(
        source_file, items, premis, premis_namespace,
        premisxml, representation_uuid, sequence
    ):
    video_files = get_input(source_file)
    mediainfo_counter = 1
    image_uuids = []
    rep_counter = 0
    print('Generating PREMIS metadata about each file object - this may take'
          ' some time if on a network and/or working with an image sequence')
    for image in video_files:
        object_parent = create_unit(
            -1, premis, 'object'
            )
        object_identifier_uuid = create_unit(
            1, object_parent, 'objectIdentifier'
            )
        object_identifier_uuid_type = create_unit(
            1, object_identifier_uuid, 'objectIdentifierType'
            )
        object_identifier_uuid_type.text = 'UUID'
        object_identifier_uuid_value = create_unit(
            2, object_identifier_uuid, 'objectIdentifierValue'
            )
        file_uuid = str(uuid.uuid4())
        image_uuids.append(file_uuid)
        object_identifier_uuid_value.text = file_uuid
        object_category = ET.Element(
            "{%s}objectCategory" % (premis_namespace)
            )
        object_parent.insert(
            5, object_category
            )
        object_category.text = 'file'
        if rep_counter == 0:
            root_uuid = file_uuid
        rep_counter += 1
        format_ = ET.Element("{%s}format" % (premis_namespace))
        object_characteristics = create_unit(
            10, object_parent, 'objectCharacteristics'
            )
        object_characteristics.insert(2, format_)
        mediainfo = subprocess.check_output(
            ['mediainfo', '--Output=PBCore2', image]
            )
        parser = ET.XMLParser(
            remove_blank_text=True, remove_comments=True
            )
        mediainfo_xml = ET.fromstring((mediainfo), parser=parser)
        fixity = create_unit(
            0, object_characteristics, 'fixity'
            )
        size = create_unit(
            1, object_characteristics, 'size'
            )
        size.text = str(os.path.getsize(image))
        format_designation = create_unit(
            0, format_, 'formatDesignation'
            )
        format_name = create_unit(
            1, format_designation, 'formatName'
            )
        format_name_mediainfo = subprocess.check_output(
            ['mediainfo', '--Inform=General;%InternetMediaType%', image]
            ).rstrip()
        if format_name_mediainfo == '':
            format_name_mediainfo = subprocess.check_output(
                ['mediainfo', '--Inform=General;%Format_Commercial%', image]
                ).rstrip()
        format_name.text = format_name_mediainfo
        message_digest_algorithm = create_unit(
            0, fixity, 'messageDigestAlgorithm'
            )
        message_digest = create_unit(
            1, fixity, 'messageDigest'
            )
        message_digestOriginator = create_unit(
            2, fixity, 'messageDigestOriginator'
            )
        message_digestOriginator.text = 'internal'
        object_characteristicsExtension = create_unit(
            4, object_characteristics, 'objectCharacteristicsExtension'
            )
        object_characteristicsExtension.insert(
            mediainfo_counter, mediainfo_xml
            )
        relationship = create_unit(
            7, object_parent, 'relationship'
            )
        relatedObjectIdentifier = create_unit(
            2, relationship, 'relatedObjectIdentifier'
            )
        relatedObjectIdentifierType = create_unit(
            2, relatedObjectIdentifier, 'relatedObjectIdentifierType'
            )
        relatedObjectIdentifierType.text = 'UUID'
        relatedObjectIdentifierValue = create_unit(
            3, relatedObjectIdentifier, 'relatedObjectIdentifierValue'
            )
        relatedObjectIdentifierValue.text = representation_uuid
        if sequence == 'sequence':
            relatedObjectSequence = create_unit(
                4, relationship, 'relatedObjectSequence'
                )
            relatedObjectSequence.text = str(mediainfo_counter)
        relationshipType = create_unit(
            0, relationship, 'relationshipType'
            )
        relationshipType.text = 'structural'
        relationshipSubType = create_unit(
            1, relationship, 'relationshipSubType'
            )
        relationshipSubType.text = 'is included in'
        # this is a total hack. if sequence = loopline', do not generate hash as it already exists in manifest :(
        # looks like loopline isn't the keyword any longer. it's len = 32?
        if not len(sequence) == 32:
            md5_output = hashlib_md5(source_file, image)
            message_digest.text = md5_output
        else:
            message_digest.text = sequence
        message_digest_algorithm.text = 'md5'
        mediainfo_counter += 1
    # When the image info has been grabbed, add info about the representation to the wav file. This may be problematic if makedpx is run first..
    doc = ET.ElementTree(premis)
    xml_info = [doc, premisxml, root_uuid, sequence, image_uuids]
    return xml_info
def make_event(
        premis, event_type, event_detail,
        agentlist, event_id, event_linking_object_identifier,
        event_linking_object_role, event_time
    ):
    # This is really only here because the premis.py version handles the \
    # linkingAgentIdentifiers differently.
    premis_namespace = "http://www.loc.gov/premis/v3"
    event = ET.SubElement(premis, "{%s}event" % (premis_namespace))
    premis.insert(-1, event)
    event_Identifier = create_unit(1, event, 'eventIdentifier')
    event_id_type = ET.Element("{%s}eventIdentifierType" % (premis_namespace))
    event_Identifier.insert(0, event_id_type)
    event_id_value = ET.Element("{%s}eventIdentifierValue" % (premis_namespace))
    event_Identifier.insert(0, event_id_value)
    event_Type = ET.Element("{%s}eventType" % (premis_namespace))
    event.insert(2, event_Type)
    event_DateTime = ET.Element("{%s}eventDateTime" % (premis_namespace))
    event.insert(3, event_DateTime)
    if event_time == 'now':
        event_DateTime.text = time.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        event_DateTime.text = event_time
    event_Type.text = event_type
    event_id_value.text = event_id
    event_id_type.text = 'UUID'
    eventDetailInformation = create_unit(
        4, event, 'eventDetailInformation'
        )
    eventDetail = create_unit(
        0, eventDetailInformation, 'eventDetail'
        )
    eventDetail.text = event_detail
    for i in event_linking_object_identifier:
        linkingObjectIdentifier = create_unit(
            5, event, 'linkingObjectIdentifier'
            )
        linkingObjectIdentifierType = create_unit(
            0, linkingObjectIdentifier, 'linkingObjectIdentifierType'
            )
        linkingObjectIdentifierValue = create_unit(
            1, linkingObjectIdentifier, 'linkingObjectIdentifierValue'
            )
        linkingObjectIdentifierValue.text = i
        linkingObjectRole = create_unit(
            2, linkingObjectIdentifier, 'linkingObjectRole'
            )
        linkingObjectIdentifierType.text = 'UUID'
        linkingObjectRole.text = event_linking_object_role
    for i in agentlist:
        linkingAgentIdentifier = create_unit(
            -1, event, 'linkingAgentIdentifier'
            )
        linkingAgentIdentifierType = create_unit(
            0, linkingAgentIdentifier, 'linkingAgentIdentifierType'
            )
        linkingAgentIdentifierValue = create_unit(
            1, linkingAgentIdentifier, 'linkingAgentIdentifierValue'
            )
        linkingAgentIdentifierRole = create_unit(
            2, linkingAgentIdentifier, 'linkingAgentRole'
            )
        linkingAgentIdentifierRole.text = 'implementer'
        linkingAgentIdentifierType.text = 'UUID'
        linkingAgentIdentifierValue.text = i


def capture_description(
        premis, xml_info, capture_station, times, engineer
    ):
    '''
    Events:
    1. capture - glean from v210 mediainfo xml
    2. ffv1 - ffmpeg logs but get time from sip log also user input
    3. lossless verification - ffmpeg logs and time/judgement from sip log
    4. whole file manifest - sip log
    that's it?
    '''
    if engineer == 'Kieran O\'Leary':
        engineer_agent = '0b3b7e69-80e1-48ec-bf07-62b04669117d'
    elif engineer == 'Aoife Fitzmaurice':
        engineer_agent = '9e59e772-14b0-4f9e-95b3-b88b6e751c3b'
    elif engineer == 'Raelene Casey':
        engineer_agent = 'b342d3f7-d87e-4fe3-8da5-89e16a30b59e'


    capture_uuid = str(uuid.uuid4())
    if capture_station == 'es2':
        j30sdi_agent = 'e2ca7ad2-8edf-4e4e-a3c7-36e970c796c9'
        bm4k_agent = 'f47b98a2-b879-4786-9f6b-11fc3234a91e'
        edit_suite2_mac_agent = '75a0b9ff-1f04-43bd-aa87-c31b73b1b61c'
        elcapitan_agent = '68f56ede-a1cf-48aa-b1d8-dc9850d5bfcc'
        capture_agents = [
            j30sdi_agent, bm4k_agent,
            edit_suite2_mac_agent, elcapitan_agent,
            engineer_agent
            ]
    elif capture_station == 'loopline':
        m2000p_agent = '60ae3a85-b595-45e0-8e4a-b95e90a6c422'
        kona3_agent = 'c5e504ca-b4d5-410f-b87b-4b7ed794e44d'
        loopline_mac_agent = 'be3060a8-6ccf-4339-97d5-a265687c3a5a'
        osx_lion_agent = 'c5fc84fc-cc96-42a1-a5be-830b4e3012ae'
        capture_agents = [
            m2000p_agent, kona3_agent,
            loopline_mac_agent, osx_lion_agent,
            engineer_agent
            ]

    elif 'ingest1' in capture_station:
        sony510p_agent = 'dbdbb06b-ab10-49db-97a1-ff2ad285f9d2'
        sony1200p_agent = 'd13fae39-ac71-446e-88df-96c0d267b26c'
        ingest1_agent = '5fd99e09-63d7-4e9f-8383-1902f727d2a5'
        windows7_agent = '192f61b1-8130-4236-a827-a194a20557fe'
        ingest1kona_agent = 'c93ee9a5-4c0c-4670-b857-8726bfd23cae'
        if capture_station == 'ingest1-dvw':
            capture_agents = [sony510p_agent]
        elif capture_station == 'ingest1-uvw':
            capture_agents = [sony1200p_agent]
        capture_agents += [
            ingest1kona_agent,
            ingest1_agent, windows7_agent,
            engineer_agent
            ]
    make_event(
        premis, 'creation', 'tape capture',
        capture_agents, capture_uuid, xml_info[4], 'outcome', times[0]
        )
    event_dict = {}
    for agent in capture_agents:
        # Just the UUID is returned.
        event_dict[agent] = [capture_uuid]
    return event_dict


def ffv1_description(
        premis, xml_info, workstation, times, event_dict, script_user
    ):
    if script_user == 'Kieran O\'Leary':
        script_user_agent = '0b3b7e69-80e1-48ec-bf07-62b04669117d'
    elif script_user == 'Aoife Fitzmaurice':
        script_user_agent = '9e59e772-14b0-4f9e-95b3-b88b6e751c3b'
    elif script_user == 'Raelene Casey':
        script_user_agent = 'b342d3f7-d87e-4fe3-8da5-89e16a30b59e'
    transcode_uuid = str(uuid.uuid4())
    framemd5_uuid = str(uuid.uuid4())
    manifest_uuid = str(uuid.uuid4())
    if 'admin' in workstation:
        edit_suite2_mac_agent = '75a0b9ff-1f04-43bd-aa87-c31b73b1b61c'
        elcapitan_agent = '68f56ede-a1cf-48aa-b1d8-dc9850d5bfcc'
        ffv1_agents = [
            edit_suite2_mac_agent, elcapitan_agent, script_user_agent
            ]
        make_event(
            premis, 'compression',
            'transcode to FFV1/Matroska (figure out wording later)',
            ffv1_agents, transcode_uuid, xml_info[4], 'outcome', times[1]
            )

    elif 'kieranjol' in workstation:
        ingest1_agent = '5fd99e09-63d7-4e9f-8383-1902f727d2a5'
        windows7_agent = '192f61b1-8130-4236-a827-a194a20557fe'
        ffv1_agents = [
            ingest1_agent, windows7_agent, script_user_agent
            ]
        make_event(
            premis, 'compression',
            'transcode to FFV1/Matroska (figure out wording later)',
            ffv1_agents, transcode_uuid, xml_info[4], 'outcome', times[1]
            )
    elif 'kaja' in workstation:
        osx_lion_agent = 'c5fc84fc-cc96-42a1-a5be-830b4e3012ae'
        loopline_mac_agent = 'be3060a8-6ccf-4339-97d5-a265687c3a5a'
        ffv1_agents = [
            osx_lion_agent, loopline_mac_agent, script_user_agent
            ]
        make_event(
            premis, 'compression',
            'transcode to FFV1/Matroska while specifying 4:3 DAR '
            'and Top Field First interlacement',
            ffv1_agents, transcode_uuid, xml_info[4], 'outcome', times[1]
            )
    make_event(
        premis, 'fixity check',
        'lossless verification via framemd5 (figure out wording later)',
        ffv1_agents, framemd5_uuid, xml_info[4], 'source', times[3]
        )
    make_event(
        premis, 'message digest calculation',
        'whole file checksum manifest of SIP', ffv1_agents,
        manifest_uuid, xml_info[4], 'source', times[2]
        )
    for agent in ffv1_agents:
    # Just the UUID is returned. This prevents errors if the engineer and
    # script user are different
        if agent in event_dict:
            event_dict[agent] += [transcode_uuid]
            event_dict[agent] += [framemd5_uuid]
            event_dict[agent] += [manifest_uuid]
        else:
            event_dict[agent] = [transcode_uuid]
            event_dict[agent] += [framemd5_uuid]
            event_dict[agent] += [manifest_uuid]
    for agent in event_dict:
        make_agent(
            premis, event_dict[agent], agent
            )


def get_checksum(manifest):
    if os.path.isfile(manifest):
        with open(manifest, 'r') as fo:
            manifest_lines = fo.readlines()
            for md5 in manifest_lines:
                if md5[-5:].rsplit()[0] == '.mkv':
                    return md5[:32]


def get_times(sourcexml):
    mediaxml_object = ET.parse(sourcexml)
    mxml = mediaxml_object.getroot()
    # encoded date is probably better
    capture_date = mxml.xpath('//File_Modified_Date_Local')[0].text
    return capture_date


def get_capture_workstation(mediaxml):
    mediaxml_object = ET.parse(mediaxml)
    mxml = mediaxml_object.getroot()
    mediaexpress_check = len(mxml.xpath('//COMAPPLEPROAPPSLOGNOTE'))
    fcp7_check = len(mxml.xpath('//COMAPPLEFINALCUTSTUDIOMEDIAUUID'))
    if mediaexpress_check > 0:
        print 'this was probably Media Express?'
        capture_station = 'es2'
    elif fcp7_check > 0:
        print 'this was probably FCP7?'
        capture_station = 'loopline'
    else:
        # i can't find any distinctive metadata that control room writes.
        print 'this was probably Control Room?'
        capture_station = 'ingest1'
    print 'Does this sound ok? Y/N?'
    station_confirm = ''
    while station_confirm not in ('Y', 'y', 'N', 'n'):
        station_confirm = raw_input()
        if station_confirm not in ('Y', 'y', 'N', 'n'):
            print 'Incorrect input. Please enter Y or N'
        elif station_confirm not in ('Y', 'y'):
            capture_station = ''
            if capture_station not in range(1, 4):
                capture_station = raw_input(
                    '\n\n**** Where was tape captured?\n'
                    'Press 1, 2 or 3\n\n1. es2\n2. loopline\n3. ingest 1\n'
                    )
                while int(capture_station) not in range(1, 4):
                    capture_station = raw_input(
                        '\n\n**** Where was tape captured?\n'
                        'Press 1, 2 or 3\n\n1. es2\n2. loopline\n3. ingest 1\n'
                        )
            if capture_station == '1':
                capture_station = 'es2'
            elif capture_station == '2':
                capture_station = 'loopline'
            elif capture_station == '3':
                capture_station = 'ingest1'
    if capture_station == 'ingest1':
        ingest_deck = '0'
        while int(ingest_deck) not in range(1, 3):
            ingest_deck = raw_input(
                '\n\n**** Where was tape captured?\n'
                'Press 1, 2\n1. DVW-510p (Digi)\n2. UVW-1200p (BetaSP)\n'
                )
            if int(ingest_deck) not in range(1, 3):
                print 'Incorrect input. Please enter 1 or 2 plz'
                while int(ingest_deck) not in range(1, 3):
                    ingest_deck = raw_input(
                        '\n\n**** Where was tape captured?\n'
                        'Press 1, 2\n2. DVW-510p (Digi)\n3. UVW-1200p (BetaSP)\n'
                        )
            if ingest_deck == '1':
                capture_station = 'ingest1-dvw'
            elif ingest_deck == '2':
                capture_station = 'ingest1-uvw'
    return capture_station


def get_user(question):
    user = ''
    if not user == '1' or user == '2' or user == '3':
        user = raw_input(
            '\n\n%s'
            '\nPress 1 or 2 or 3\n\n'
            '1. Kieran O\'Leary\n2. Aoife Fitzmaurice\n3. Raelene Casey\n'
            % question)
        while user not in ('1', '2', '3'):
            user = raw_input(
                '\n\n%s'
                '\nPress 1 or 2 or 3\n\n'
                '1. Kieran O\'Leary\n2. Aoife Fitzmaurice\n3. Raelene Casey\n'
                % question
                )
    if user == '1':
        user = 'Kieran O\'Leary'
    elif user == '2':
        user = 'Aoife Fitzmaurice'
    elif user == '3':
        user = 'Raelene Casey'
    return user


def analyze_log(logfile):
    losslessness = ''
    framemd5_time = ''
    manifest_time = ''
    logged_workstation = ''
    with open(logfile, 'r') as fo:
        log_lines = fo.readlines()
        for line in log_lines:
            if 'Transcode was lossless' in line:
                losslessness = 'lossless'
            if 'Framemd5 generation of output file completed' in line:
                framemd5_time = line[:19]
            if 'MD5 manifest started' in line:
                manifest_time = line[:19]
        workstation = log_lines[0][20:35]
        print workstation

        return manifest_time, framemd5_time, losslessness, workstation


def main():
    script_user = get_user('**** Who is running this script?')
    engineer = get_user('**** Who captured the actual tape?')
    if not os.path.isdir(sys.argv[1]):
        print 'Input should be a directory'
        sys.exit()
    for root, dirs, filenames in os.walk(sys.argv[1]):
        for filename in filenames:
            if filename.endswith('.mkv'):
                if os.path.isfile(os.path.join(root, filename)):
                    source_file = os.path.join(root, filename)
    print 'Processing: %s' % source_file
    premisxml, premis_namespace, doc, premis = setup_xml(source_file)
    sip_dir = os.path.dirname(source_file)
    parent_dir = os.path.dirname(sip_dir)
    metadata_dir = os.path.join(parent_dir, 'metadata')
    logs_dir = os.path.join(parent_dir, 'logs')
    ffv1_xml = os.path.join(
        metadata_dir, os.path.basename(
            source_file
            + '_mediainfo.xml'
            )
        )
    # the replace here is a terrible hack. Sad! Fix!
    source_xml = os.path.join(
        metadata_dir,
        os.path.basename(
            source_file.replace('.mkv', '.mov')
            + '_source_mediainfo.xml'))
    logfile = os.path.join(
        logs_dir,
        os.path.basename(
            source_file.replace('.mkv', '.mov')
            + '_log.log'))
    capture_time = get_times(source_xml)
    transcode_time = get_times(ffv1_xml)
    manifest_time, framemd5_time, losslessness, workstation = analyze_log(logfile)
    times = [
        capture_time, transcode_time, manifest_time, framemd5_time, losslessness
        ]
    if os.path.isfile(ffv1_xml):
        capture_station = get_capture_workstation(ffv1_xml)
    else:
        print 'Can\'t find XML of FFv1 file. Exiting!'
        sys.exit()
    '''
    /home/kieranjol/ifigit/ifiscripts/massive/objects sip
    /home/kieranjol/ifigit/ifiscripts/massive parent
    '''
    manifest = parent_dir + '_manifest.md5'
    if not os.path.isfile(manifest):
        print 'no manifest found'
        sys.exit()
    md5 = get_checksum(manifest)
    # this items var is sad,clearly there's hardcoded workflow crap in premis.py
    # I don't even know if any of these are relevant anymore
    items = {
        "workflow":"raw audio",
        "oe":'n/a',
        "filmographic":'n/a',
        "sourceAccession":'unknown at present',
        "interventions":['placeholder'],
        "prepList":['placeholder'],
        "user":'n/a'
        }
    representation_uuid = str(uuid.uuid4())
    intellectual_entity_uuid = str(uuid.uuid4())
    # looks like loopline isn't the keyword any longer. it's len = 32?
    xml_info = create_object(
        source_file, items, premis,
        premis_namespace, premisxml, representation_uuid, md5
        )
    linkinguuids = [xml_info[4][0], 'n/a', 'n/a']
    create_intellectual_entity(
        premisxml, premis_namespace, doc, premis,
        items, intellectual_entity_uuid
        )
    representation_object = create_representation(
        premisxml, premis_namespace, doc, premis,
        items, linkinguuids, representation_uuid, 'no_sequence', 'n/a'
        )
    event_dict = capture_description(
        premis, xml_info, capture_station, times, engineer
        )
    ffv1_description(
        premis, xml_info, workstation, times, event_dict, script_user
        )
    write_premis(doc, premisxml)

if __name__ == '__main__':
    main()