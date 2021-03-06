#!/usr/bin/env python
"""
_LoadDBSFilesByDAS_

MySQL implementation of LoadDBSFilesByDAS
"""

from WMCore.Database.DBFormatter import DBFormatter

class LoadDBSFilesByDAS(DBFormatter):
    fileInfoSQL = """SELECT dbsbuffer_file.id AS id,
                            dbsbuffer_file.lfn AS lfn,
                            dbsbuffer_file.filesize AS filesize,
                            dbsbuffer_file.events AS events,
                            dbsbuffer_file.status AS status,
                            dbsbuffer_file.block_id AS block,
                            dbsbuffer_algo.app_name AS app_name,
                            dbsbuffer_algo.app_ver AS app_ver,
                            dbsbuffer_algo.app_fam AS app_fam,
                            dbsbuffer_algo.pset_hash AS pset_hash,
                            dbsbuffer_algo.config_content,
                            dbsbuffer_dataset.path AS dataset_path,
                            dbsbuffer_dataset.global_tag AS global_tag,
                            dbsbuffer_dataset.prep_id AS prep_id,
                            dbsbuffer_workflow.name AS workflow,
                            dbsbuffer_workflow.block_close_max_wait_time,
                            dbsbuffer_workflow.block_close_max_files,
                            dbsbuffer_workflow.block_close_max_events,
                            dbsbuffer_workflow.block_close_max_size
                     FROM dbsbuffer_file
                     INNER JOIN dbsbuffer_algo_dataset_assoc ON
                       dbsbuffer_file.dataset_algo = dbsbuffer_algo_dataset_assoc.id
                     INNER JOIN dbsbuffer_algo ON
                       dbsbuffer_algo_dataset_assoc.algo_id = dbsbuffer_algo.id
                     INNER JOIN dbsbuffer_dataset ON
                       dbsbuffer_algo_dataset_assoc.dataset_id = dbsbuffer_dataset.id AND
                       dbsbuffer_dataset.path = :datasetpath
                     INNER JOIN dbsbuffer_workflow ON
                       dbsbuffer_workflow.id = dbsbuffer_file.workflow
                     WHERE dbsbuffer_file.status = 'NOTUPLOADED'
                     AND NOT EXISTS ( SELECT *
                                      FROM dbsbuffer_file_parent
                                      INNER JOIN dbsbuffer_file parent_file ON
                                        parent_file.id = dbsbuffer_file_parent.parent AND
                                        parent_file.status = 'NOTUPLOADED'
                                      WHERE dbsbuffer_file_parent.child = dbsbuffer_file.id )
                     ORDER BY dbsbuffer_file.id
                     """

    getLocationSQL = """SELECT dbsbuffer_location.pnn as location, dbsbuffer_file.id as id
                          FROM dbsbuffer_location
                          INNER JOIN dbsbuffer_file_location dfl ON dfl.location = dbsbuffer_location.id
                          INNER JOIN dbsbuffer_file ON dbsbuffer_file.id = dfl.filename
                          WHERE dbsbuffer_file.id = :fileid"""


    getChecksumSQL = """SELECT cst.type AS cktype, fcs.cksum AS cksum, fcs.fileid AS id FROM
                           dbsbuffer_file_checksums fcs INNER JOIN
                           dbsbuffer_checksum_type cst ON fcs.typeid = cst.id
                           WHERE fcs.fileid = :fileid"""


    getRunLumiSQL = """SELECT flr.run AS run, flr.lumi AS lumi, flr.num_events AS num_events, dbsbuffer_file.id AS id
                          FROM dbsbuffer_file_runlumi_map flr
                          INNER JOIN dbsbuffer_file ON dbsbuffer_file.id = flr.filename
                          WHERE dbsbuffer_file.id = :fileid"""


    getParentLFNSQL = """SELECT dbfa.lfn AS lfn, dbfb.id AS id FROM dbsbuffer_file dbfa
                            INNER JOIN dbsbuffer_file_parent dfp ON dfp.parent = dbfa.id
                            INNER JOIN dbsbuffer_file dbfb ON dfp.child = dbfb.id
                            WHERE dbfb.id = :fileid """






    def formatFileInfo(self, result):
        """
        _formatFileInfo_

        Some databases (Oracle) aren't case sensitive with respect to column
        names so we'll do some formatting so the column names are returned as
        expected.
        """
        resultList = self.formatDict(result)

        for resultDict in resultList:
            resultDict["appName"] = resultDict["app_name"]
            del resultDict["app_name"]

            resultDict["appVer"] = resultDict["app_ver"]
            del resultDict["app_ver"]

            resultDict["appFam"] = resultDict["app_fam"]
            del resultDict["app_fam"]

            resultDict["psetHash"] = resultDict["pset_hash"]
            del resultDict["pset_hash"]

            resultDict["configContent"] = resultDict["config_content"]
            del resultDict["config_content"]

            resultDict["datasetPath"] = resultDict["dataset_path"]
            del resultDict["dataset_path"]

            resultDict["size"] = resultDict["filesize"]
            del resultDict["filesize"]

            resultDict["globalTag"] = resultDict['global_tag']
            del resultDict['global_tag']

        return resultList


    def locInfo(self, result):
        """
        Format the location info so that it matches

        """

        resultList = self.formatDict(result)

        interimDictionary = {}

        for entry in resultList:
            if entry['id'] not in interimDictionary:
                interimDictionary[entry['id']] = set()
            interimDictionary[entry['id']].add(entry['location'])


        finalList = []
        for entry in interimDictionary:
            tmpDict = {'id': entry, 'locations': interimDictionary[entry]}
            finalList.append(tmpDict)


        return finalList



    def ckInfo(self, result):
        """
        Assemble the checksums into the appropriate format.

        """


        resultList = self.formatDict(result)

        interimDictionary = {}

        for entry in resultList:
            if entry['id'] not in interimDictionary:
                interimDictionary[entry['id']] = {}
            interimDictionary[entry['id']][entry['cktype']] = entry['cksum']


        finalList = []
        for entry in interimDictionary:
            tmpDict = {'id': entry, 'checksums': interimDictionary[entry]}
            finalList.append(tmpDict)


        return finalList


    def runInfo(self, result):
        """
        Assemble runLumis into the appropriate format

        """

        resultList = self.formatDict(result)

        interimDictionary = {}

        for entry in resultList:
            if entry['id'] not in interimDictionary:
                interimDictionary[entry['id']] = {}
            if entry['run'] not in interimDictionary[entry['id']]:
                interimDictionary[entry['id']][entry['run']] = []
            interimDictionary[entry['id']][entry['run']].append((entry['lumi'], entry["num_events"]))

        finalList = []
        for entry in interimDictionary:
            tmpDict = {'id': entry, 'runInfo': interimDictionary[entry]}
            finalList.append(tmpDict)


        return finalList


    def parentInfo(self, result):
        """
        Format the parent info so that it makes sense

        """

        resultList = self.formatDict(result)

        interimDictionary = {}

        for entry in resultList:
            if entry['id'] not in interimDictionary:
                interimDictionary[entry['id']] = []
            interimDictionary[entry['id']].append(entry['lfn'])


        finalList = []
        for entry in interimDictionary:
            tmpDict = {'id': entry, 'parentLFNs': interimDictionary[entry]}
            finalList.append(tmpDict)


        return finalList



    def getBinds(self, files):
        binds = []
        files = self.dbi.makelist(files)
        for f in files:
            binds.append({'fileid': f})
        return binds

    def execute(self, datasetpath, conn = None, transaction = False):
        """
        Execute multiple SQL queries to extract all binding information
        Use the first query to get the fileIDs

        """
        result   = self.dbi.processData(self.fileInfoSQL,
                                        { 'datasetpath' : datasetpath },
                                        conn = conn,
                                        transaction = transaction)
        fileInfo = self.formatFileInfo(result)

        fileIDs  = [x['id'] for x in fileInfo]
        binds    = self.getBinds(fileIDs)

        if len(fileInfo) == 0:
            # Then we have no files for this DAS
            return []


        # Do locations
        result   = self.dbi.processData(self.getLocationSQL, binds,
                                        conn = conn,
                                        transaction = transaction)
        locInfo  = self.locInfo(result)
        fullResults = self.merge(fileInfo, locInfo)


        # Do checksums
        result   = self.dbi.processData(self.getChecksumSQL, binds,
                                        conn = conn,
                                        transaction = transaction)

        ckInfo      = self.ckInfo(result)
        fullResults = self.merge(fullResults, ckInfo)


        # Do runLumi
        result      = self.dbi.processData(self.getRunLumiSQL, binds,
                                           conn = conn,
                                           transaction = transaction)
        runInfo  = self.runInfo(result)
        fullResults = self.merge(fullResults, runInfo)



        # Do parents
        result   = self.dbi.processData(self.getParentLFNSQL, binds,
                                        conn = conn,
                                        transaction = transaction)
        parInfo  = self.parentInfo(result)
        fullResults = self.merge(fullResults, parInfo)



        return fullResults


    def merge(self, listA, listB, field = 'id'):
        """
        _merge_

        Merge together two file lists based on the ID field
        """

        for entryA in listA:
            for entryB in listB:
                if entryA[field] == entryB[field]:
                    # Then we've found a match
                    entryA.update(entryB)
                    break


        return listA


    def groupByID(self, inputList, key):
        """
        Group all the entries in a list of dictionaries together by ID


        """

        interimDictionary = {}

        for entry in inputList:
            if entry['id'] not in interimDictionary:
                interimDictionary[entry['id']] = set()
            interimDictionary[entry['id']].add(entry[key])


        finalList = []
        for entry in interimDictionary:
            tmpDict = {'id': entry, key: interimDictionary[entry]}
            finalList.append(tmpDict)


        return finalList
